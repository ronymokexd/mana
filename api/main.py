from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import psycopg2.extras
import uvicorn

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
        user="mana_qkne_user",      # cámbialo por tu usuario exacto de Render
        password="aXd4FQSFS06Tje19YezEAHwcNOprcqk1",  # tu contraseña exacta
        cursor_factory=psycopg2.extras.RealDictCursor
    )

# -------------------- LOGIN --------------------
class Login(BaseModel):
    usuario: str
    contraseña: str

@app.post("/login")
def login_admin(datos: Login):
    conexion = conexion_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            "SELECT * FROM administrador WHERE usuario=%s AND contraseña=%s",
            (datos.usuario, datos.contraseña)
        )
        admin = cursor.fetchone()
        if admin:
            return {"mensaje": "Inicio de sesión exitoso", "admin": admin}
        else:
            raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

# -------------------- USUARIOS --------------------
@app.get("/usuarios")
def obtener_usuarios():
    conexion = conexion_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT * FROM administrador")
        usuarios = cursor.fetchall()
        return usuarios
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

# -------------------- MENÚ --------------------
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
        raise HTTPException(status_code=500, detail=str(e))
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
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

# -------------------- CLIENTES --------------------
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
        # Consulta modificada para usar RETURNING id (obligatorio en PostgreSQL)
        cursor.execute(
            "INSERT INTO clientes (nombre, numero, direccion, barrio) VALUES (%s, %s, %s, %s) RETURNING id",
            (datos.nombre, datos.numero, datos.direccion, datos.barrio)
        )
        # Obtenemos el ID de la fila devuelta
        nuevo_id = cursor.fetchone()['id']
        conexion.commit()
        
        # Devolvemos el ID al cliente (frontend)
        return {"mensaje": "Cliente registrado exitosamente", "id": nuevo_id}
        
    except Exception as e:
        conexion.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

@app.get("/clientes")
def obtener_clientes():
    # ... (Esta función se mantiene igual, ya que solo lista)
    conexion = conexion_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT * FROM clientes")
        clientes = cursor.fetchall()
        return clientes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexion.close()
# -------------------- PEDIDOS --------------------
class PedidoItem(BaseModel):
    producto_id: int
    nombre_producto: str
    precio: int
    cantidad: int

class Pedido(BaseModel):
    cliente_id: int
    items: list[PedidoItem]
    metodo_pago: str
    necesita_cambio: int | None = None
    descripcion: str | None = None

@app.post("/pedidos")
def crear_pedido(pedido: Pedido):
    conexion = conexion_bd()
    cursor = conexion.cursor()

    try:
        # Insertar productos del pedido
        for item in pedido.items:
            cursor.execute("""
                INSERT INTO pedidos_enviados 
                (cliente_id, producto_id, nombre_producto, precio, cantidad, metodo_pago, necesita_cambio, descripcion)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                pedido.cliente_id,
                item.producto_id,
                item.nombre_producto,
                item.precio,
                item.cantidad,
                pedido.metodo_pago,
                pedido.necesita_cambio,
                pedido.descripcion
            ))

        conexion.commit()
        numero_pedido = cursor.lastrowid  # Usamos el ID como número de pedido

        return {"mensaje": "Pedido creado exitosamente", "numero_pedido": numero_pedido}

    except Exception as e:
        conexion.rollback()
        return {"error": str(e)}

    finally:
        cursor.close()
        conexion.close()

@app.get("/pedidos")
def obtener_pedidos():
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
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

# -------------------- REINICIAR PEDIDOS --------------------
@app.post("/reiniciar-pedidos")
def reiniciar_pedidos():
    conexion = conexion_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute("DELETE FROM pedidos_enviados;")
        cursor.execute("ALTER TABLE pedidos_enviados AUTO_INCREMENT = 1;")
        conexion.commit()
        return {"mensaje": "Pedidos eliminados y contador de ID reiniciado a 1"}
    except Exception as e:
        conexion.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

# -------------------- CARRITO --------------------
class CarritoItem(BaseModel):
    producto_id: int
    nombre_producto: str
    precio: int
    cantidad: int

@app.post("/carrito")
def agregar_al_carrito(item: CarritoItem):
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
        raise HTTPException(status_code=500, detail=str(e))
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
        raise HTTPException(status_code=500, detail=str(e))
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
        raise HTTPException(status_code=500, detail=str(e))
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
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

@app.get("/pedidos_enviados")
def obtener_pedidos_enviados():
    conexion = conexion_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute("""
            SELECT 
                p.id AS id,
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
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexion.close()
@app.delete("/reiniciar_pedidos")
def reiniciar_pedidos():
    conexion = conexion_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute("DELETE FROM pedidos_enviados;")
        cursor.execute("ALTER TABLE pedidos_enviados AUTO_INCREMENT = 1;")
        conexion.commit()
        return {"mensaje": "Pedidos eliminados y contador de ID reiniciado a 1"}
    except Exception as e:
        conexion.rollback()
        raise HTTPException(status_code=500, detail=str(e))
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
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexion.close()
        
@app.get("/estadisticas_dia")
def estadisticas_dia():
    conexion = conexion_bd()
    cursor = conexion.cursor()
    try:
        # Total de pedidos del día (No genera error)
        cursor.execute("SELECT COUNT(*) AS total_pedidos FROM pedidos_enviados")
        total_pedidos = cursor.fetchone()['total_pedidos']

        # Total por categoría (No genera error, agrupa solo por cat.nombre)
        cursor.execute("""
            SELECT cat.nombre AS categoria, SUM(p.cantidad) AS total
            FROM pedidos_enviados p
            JOIN productos pr ON p.producto_id = pr.id
            JOIN categorias cat ON pr.categoria_id = cat.id
            GROUP BY cat.nombre
        """)
        productos_por_categoria = cursor.fetchall()

        # Producto más vendido (*** CONSULTA CORREGIDA PARA POSTGRESQL ***)
        # Se agregan pr.nombre y cat.nombre al GROUP BY, además de pr.id
        cursor.execute("""
            SELECT pr.nombre, cat.nombre AS categoria, SUM(p.cantidad) AS cantidad
            FROM pedidos_enviados p
            JOIN productos pr ON p.producto_id = pr.id
            JOIN categorias cat ON pr.categoria_id = cat.id
            GROUP BY pr.id, pr.nombre, cat.nombre  # <<-- AJUSTE CLAVE AQUÍ
            ORDER BY cantidad DESC
            LIMIT 1
        """)
        producto_mas_vendido = cursor.fetchone() or {"nombre": "N/A", "categoria": "N/A", "cantidad": 0}

        # Método de pago más usado (No genera error)
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
        # Es útil devolver el error real para depuración, pero mantengo el formato original
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexion.close()


# -------------------- EJECUCIÓN --------------------
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.0", port=8000)
