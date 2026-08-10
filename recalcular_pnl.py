import sqlite3
from decimal import Decimal

DB_PATH = "crypto_crm.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Obtener todos los clientes
    cursor.execute("SELECT id, symbol FROM clientes_cripto")
    clientes = cursor.fetchall()

    for cliente_id, symbol in clientes:
        cursor.execute(
            """
            SELECT COALESCE(SUM(pnl_realizado), 0)
            FROM interacciones
            WHERE cliente_id = ? AND tipo = 'venta'
            """,
            (cliente_id,),
        )
        pnl_acumulado = cursor.fetchone()[0] or 0

        cursor.execute(
            """
            UPDATE clientes_cripto
            SET pnl_realizado_acumulado = ?
            WHERE id = ?
            """,
            (str(Decimal(str(pnl_acumulado))), cliente_id),
        )
        print(f"  {symbol}: pnl_realizado_acumulado = {pnl_acumulado}")

    conn.commit()
    conn.close()
    print("\nRecalculo completado. Reinicia la API.")

if __name__ == "__main__":
    main()