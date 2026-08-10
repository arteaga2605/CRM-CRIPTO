import sqlite3
import os

DB_PATH = "crypto_crm.db"

def main():
    if not os.path.exists(DB_PATH):
        print(f"No se encontro {DB_PATH}. No hay nada que migrar.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(clientes_cripto)")
    columnas = [col[1] for col in cursor.fetchall()]

    if "pnl_realizado_acumulado" not in columnas:
        cursor.execute(
            "ALTER TABLE clientes_cripto ADD COLUMN pnl_realizado_acumulado NUMERIC(20,8) DEFAULT 0"
        )
        conn.commit()
        print("OK: Columna 'pnl_realizado_acumulado' agregada.")
    else:
        print("La columna ya existe. No se hicieron cambios.")

    conn.close()

if __name__ == "__main__":
    main()