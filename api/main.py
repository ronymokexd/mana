from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import psycopg2.extras
import uvicorn
from datetime import datetime, timedelta
from typing import Annotated, Optional
import os

# PIN para operaciones sensibles (mejor: definir DELETE_PIN en env vars)
DELETE_PIN = os.getenv("DELETE_PIN", "1234")


# 🛑 IMPORTACIONES PARA SEGURIDAD JWT
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

# -------------------- CONFIGURACIÓN DE SEGURIDAD --------------------
# ⚠️ CAMBIA ESTO POR UNA CLAVE SECRETA FUERTE ANTES DE PRODUCCIÓN
SECRET_KEY = "Mokerony22!" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
ADMIN_TOKEN_EXPIRE_MINUTES = 60 * 24

# Esquema para indicar dónde obtener el token (Header Authorization: Bearer <token>)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login") 

# -------------------- FUNCIONES DE SEGURIDAD --------------------

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Genera un Token JWT firmado."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    """Decodifica el Token JWT y devuelve el 'sub' (ID) si es válido."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
        return user_id # Devuelve el ID
    except JWTError:
        return None

def get_current_cliente(token: Annotated[str, Depends(oauth2_scheme)]):
    """Dependencia para validar el token y obtener los datos del cliente."""
    client_id = decode_access_token(token)
    if client_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Busca el cliente en la BD
    conexion = conexion_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT id, nombre, numero, direccion, barrio FROM clientes WHERE id = %s", (client_id,))
        cliente = cursor.fetchone()
        if cliente is None:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        # Retornamos un diccionario con los datos del cliente, incluyendo el ID
        return dict(cliente)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error de base de datos al buscar cliente")
    finally:
        cursor.close()
        conexion.close()

# -------------------- INICIALIZACIÓN DE FASTAPI --------------------
app = FastAPI()

# -------------------- CORS --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- CONEXIÓN A BD --------------------
def conexion_bd():
    return psycopg2.connect(
        host="dpg-d471s46mcj7s73dfaag0-a.oregon-postgres.render.com",
        database="mana_qkne",
        user="mana_qkne_user",
        password="aXd4FQSFS06Tje19YezEAHwcNOprcqk1",
        cursor_factory=psycopg2.extras.RealDictCursor
    )

# ---------------------------------------------------------------------------------------------------
# -------------------- ENDPOINTS DE AUTENTICACIÓN Y CLIENTES --------------------
# ---------------------------------------------------------------------------------------------------

class Login(BaseModel):
    usuario: str
    contraseña: str

@app.post("/login")
def login_admin(datos: Login):
    conexion = conexion_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            "SELECT id, usuario, rol FROM administrador WHERE usuario=%s AND contraseña=%s",
            (datos.usuario, datos.contraseña)
        )
        admin = cursor.fetchone()
        if admin:
            # 🛑 Generar token para Admin
            access_token_expires = timedelta(minutes=ADMIN_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": str(admin['id']), "rol": "admin"},
                expires_delta=access_token_expires
            )
            return {
                "mensaje": "Inicio de sesión exitoso",
                "admin": admin,
                "access_token": access_token,
                "token_type": "bearer"
            }
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario o contraseña incorrectos")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

# --- CLIENTES ---

class Cliente(BaseModel):
    nombre: str
    numero: str
    direccion: str
    barrio: str

@app.post("/clientes")
def crear_cliente(datos: Cliente):
    conexion = conexion_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            "INSERT INTO clientes (nombre, numero, direccion, barrio) VALUES (%s, %s, %s, %s) RETURNING id",
            (datos.nombre, datos.numero, datos.direccion, datos.barrio)
        )
        nuevo_id = cursor.fetchone()['id']
        conexion.commit()
        
        # 🛑 Generar token para el Cliente recién creado
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(nuevo_id), "rol": "cliente"},
            expires_delta=access_token_expires
        )
        
        # Devolver ID y TOKEN
        return {
            "mensaje": "Cliente registrado exitosamente", 
            "id": nuevo_id,
            "access_token": access_token, 
            "token_type": "bearer"
        }
        
    except Exception as e:
        conexion.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

@app.get("/clientes/me")
def obtener_cliente_actual(cliente_actual: Annotated[dict, Depends(get_current_cliente)]):
    """Devuelve los datos del cliente actual usando el Token Bearer (usado por el frontend del carrito)."""
    return cliente_actual

@app.get("/clientes") # Se mantiene el endpoint original para listar (sin protección de token)
def obtener_clientes():
    conexion = conexion_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT * FROM clientes")
        clientes = cursor.fetchall()
        return clientes
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

# --- USUARIOS (ADMIN) ---

@app.get("/usuarios")
def obtener_usuarios():
    # Nota: Esta ruta debería protegerse con un rol de administrador
    conexion = conexion_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT * FROM administrador")
        usuarios = cursor.fetchall()
        return usuarios
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

# ---------------------------------------------------------------------------------------------------
# -------------------- ENDPOINTS DE PEDIDOS Y MENÚ --------------------
# ---------------------------------------------------------------------------------------------------

# --- MENÚ ---

class Producto(BaseModel):
    id: int
    nombre: str
    precio: int
    descripcion: str | None = None
    imagen: str | None = None
    categoria: str

@app.get("/menu")
def obtener_menu():
    conexion = conexion_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute("""
            SELECT p.id, p.nombre, p.precio, p.descripcion, p.imagen, c.nombre AS categoria
            FROM productos p
            JOIN categorias c ON p.categoria_id = c.id
            ORDER BY c.id, p.id;
        """)
        productos = cursor.fetchall()
        return productos if productos else {"mensaje": "No hay productos disponibles"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

@app.get("/menu/{nombre_categoria}")
def obtener_por_categoria(nombre_categoria: str):
    conexion = conexion_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute("""
            SELECT p.id, p.nombre, p.precio, p.descripcion, p.imagen, c.nombre AS categoria
            FROM productos p
            JOIN categorias c ON p.categoria_id = c.id
            WHERE LOWER(c.nombre) = LOWER(%s)
            ORDER BY p.id;
        """, (nombre_categoria,))
        productos = cursor.fetchall()
        return productos if productos else {"mensaje": f"No hay productos en la categoría '{nombre_categoria}'"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

@app.get("/categorias")
def obtener_categorias():
    conexion = conexion_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT * FROM categorias ORDER BY id;")
        categorias = cursor.fetchall()
        return categorias
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        cursor.close()
        conexion.close()
        
# --- PEDIDOS ---

class PedidoItem(BaseModel):
    producto_id: int
    nombre_producto: str
    precio: int
    cantidad: int

class Pedido(BaseModel):
    # Ya NO se necesita cliente_id en el body, se obtiene del token.
    items: list[PedidoItem]
    metodo_pago: str
    necesita_cambio: int | None = None
    descripcion: str | None = None

@app.post("/pedidos")
def crear_pedido(
    pedido: Pedido,
    cliente_actual: Annotated[dict, Depends(get_current_cliente)]
):
    conexion = conexion_bd()
    cursor = conexion.cursor()
    cliente_id = cliente_actual['id']

    try:
        # 1️⃣ Obtener último pedido para generar número_pedido
        cursor.execute("""
            SELECT cliente_id, numero_pedido
            FROM pedidos_enviados
            ORDER BY id DESC
            LIMIT 1
        """)
        ultimo = cursor.fetchone()

        if ultimo:
            # Si numero_pedido está en NULL → usar 1
            ultimo_numero = ultimo['numero_pedido'] if ultimo['numero_pedido'] is not None else 1

            if ultimo['cliente_id'] == cliente_id:
                numero_generado = ultimo_numero
            else:
                numero_generado = ultimo_numero + 1
        else:
            numero_generado = 1

        # 2️⃣ Insertar cada item con su número_pedido
        for item in pedido.items:
            cursor.execute("""
                INSERT INTO pedidos_enviados
                (cliente_id, producto_id, nombre_producto, precio, cantidad, metodo_pago, necesita_cambio, descripcion, numero_pedido)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                cliente_id,
                item.producto_id,
                item.nombre_producto,
                item.precio,
                item.cantidad,
                pedido.metodo_pago,
                pedido.necesita_cambio,
                pedido.descripcion,
                numero_generado
            ))

        conexion.commit()
        return {"mensaje": "Pedido creado correctamente", "numero_pedido": numero_generado}

    except Exception as e:
        conexion.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

    finally:
        cursor.close()
        conexion.close()


@app.get("/pedidos")
def obtener_pedidos():
    # Nota: Esta ruta debería protegerse con un rol de administrador
    conexion = conexion_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute("""
            SELECT 
                p.id AS numero_pedido,
                c.nombre AS cliente, 
                p.nombre_producto, 
                p.precio, 
                p.cantidad, 
                p.metodo_pago, 
                p.necesita_cambio, 
                p.descripcion,
                p.fecha
            FROM pedidos_enviados p
            JOIN clientes c ON p.cliente_id = c.id
            ORDER BY p.fecha DESC
        """)
        pedidos = cursor.fetchall()
        return pedidos
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

# -------------------- CARRITO (Se mantiene sin protección, ya que el frontend usa localStorage) --------------------
class CarritoItem(BaseModel):
    producto_id: int
    nombre_producto: str
    precio: int
    cantidad: int

@app.post("/carrito")
def agregar_al_carrito(item: CarritoItem):
    # Nota: Si quisieras proteger esta ruta y usar una tabla 'carrito' en BD,
    # necesitarías un campo 'cliente_id' y usar Depends(get_current_cliente)
    conexion = conexion_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute("""
            INSERT INTO carrito (producto_id, nombre_producto, precio, cantidad)
            VALUES (%s, %s, %s, %s)
        """, (item.producto_id, item.nombre_producto, item.precio, item.cantidad))
        conexion.commit()
        return {"mensaje": "Producto agregado al carrito"}
    except Exception as e:
        conexion.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

@app.get("/carrito")
def obtener_carrito():
    conexion = conexion_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT * FROM carrito")
        carrito = cursor.fetchall()
        return carrito
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

@app.delete("/carrito/{id}")
def eliminar_item_carrito(id: int):
    conexion = conexion_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute("DELETE FROM carrito WHERE id = %s", (id,))
        conexion.commit()
        return {"mensaje": "Producto eliminado del carrito"}
    except Exception as e:
        conexion.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

@app.delete("/carrito")
def vaciar_carrito():
    conexion = conexion_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute("DELETE FROM carrito")
        conexion.commit()
        return {"mensaje": "Carrito vaciado correctamente"}
    except Exception as e:
        conexion.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

# -------------------- ADMINISTRACIÓN Y ESTADÍSTICAS --------------------

@app.post("/reiniciar-pedidos")
@app.delete("/reiniciar_pedidos") # Se mantiene el endpoint delete para compatibilidad
def reiniciar_pedidos():
    # Nota: Esta ruta debería protegerse con un rol de administrador
    conexion = conexion_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute("DELETE FROM pedidos_enviados;")
        # En PostgreSQL, para reiniciar la secuencia de una tabla (similar a AUTO_INCREMENT)
        cursor.execute("SELECT setval(pg_get_serial_sequence('pedidos_enviados', 'id'), 1, false);") 
        conexion.commit()
        return {"mensaje": "Pedidos eliminados y contador de ID reiniciado a 1"}
    except Exception as e:
        conexion.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

@app.get("/pedidos_enviados")
def obtener_pedidos_enviados():
    """
    Devuelve todos los pedidos con información completa,
    incluyendo el id_cliente para poder agruparlos desde el frontend.
    Ahora también incluye numero_pedido para tener un consecutivo real.
    """
    conexion = conexion_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute("""
            SELECT 
                p.id AS id,
                p.numero_pedido,          
                p.cliente_id AS id_cliente,
                c.nombre AS cliente,
                c.numero,
                c.direccion,
                c.barrio,
                pr.nombre AS producto,
                cat.nombre AS categoria,
                p.cantidad,
                (p.precio * p.cantidad) AS total,
                p.metodo_pago,
                p.necesita_cambio,
                p.descripcion,
                p.fecha
            FROM pedidos_enviados p
            JOIN clientes c ON p.cliente_id = c.id
            JOIN productos pr ON p.producto_id = pr.id
            JOIN categorias cat ON pr.categoria_id = cat.id
            ORDER BY p.fecha DESC
        """)
        
        pedidos = cursor.fetchall()
        return pedidos

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    finally:
        cursor.close()
        conexion.close()



@app.get("/estadisticas_dia")
def estadisticas_dia():
    # Nota: Esta ruta debería protegerse con un rol de administrador
    conexion = conexion_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT COUNT(*) AS total_pedidos FROM pedidos_enviados")
        total_pedidos = cursor.fetchone()['total_pedidos']

        cursor.execute("""
            SELECT cat.nombre AS categoria, SUM(p.cantidad) AS total
            FROM pedidos_enviados p
            JOIN productos pr ON p.producto_id = pr.id
            JOIN categorias cat ON pr.categoria_id = cat.id
            GROUP BY cat.nombre
        """)
        productos_por_categoria = cursor.fetchall()

        cursor.execute("""
            SELECT pr.nombre, cat.nombre AS categoria, SUM(p.cantidad) AS cantidad
            FROM pedidos_enviados p
            JOIN productos pr ON p.producto_id = pr.id
            JOIN categorias cat ON pr.categoria_id = cat.id
            GROUP BY pr.id, pr.nombre, cat.nombre 
            ORDER BY cantidad DESC
            LIMIT 1
        """)
        producto_mas_vendido = cursor.fetchone() or {"nombre": "N/A", "categoria": "N/A", "cantidad": 0}

        cursor.execute("""
            SELECT metodo_pago, COUNT(*) AS total
            FROM pedidos_enviados
            GROUP BY metodo_pago
            ORDER BY total DESC
            LIMIT 1
        """)
        metodo_pago = cursor.fetchone()
        metodo_pago_mas_usado = metodo_pago['metodo_pago'] if metodo_pago else "N/A"

        return {
            "total_pedidos": total_pedidos,
            "productos_por_categoria": productos_por_categoria,
            "producto_mas_vendido": producto_mas_vendido,
            "metodo_pago_mas_usado": metodo_pago_mas_usado
        }

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        cursor.close()
        conexion.close()
class EliminarPedidoBody(BaseModel):
    numero_pedido: int
    pin: str

@app.delete("/pedidos/eliminar_por_numero")
def eliminar_pedido_por_numero(body: EliminarPedidoBody):
    # Validar PIN
    if body.pin != DELETE_PIN:
        raise HTTPException(status_code=401, detail="PIN incorrecto")

    conexion = conexion_bd()
    cursor = conexion.cursor()

    try:
        # DELETE con RETURNING devuelve tuplas
        cursor.execute("""
            DELETE FROM pedidos_enviados
            WHERE numero_pedido = %s
            RETURNING id;
        """, (body.numero_pedido,))

        eliminados = cursor.fetchall()
        conexion.commit()

        if not eliminados:
            return {"mensaje": "No se encontró ningún pedido con ese numero_pedido", "eliminados": 0}

        return {
            "mensaje": f"Pedido {body.numero_pedido} eliminado correctamente",
            "eliminados": len(eliminados),
            "ids_eliminados": [fila[0] for fila in eliminados]
        }

    except Exception as e:
        conexion.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conexion.close()

