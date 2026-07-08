from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional

from app.models import InversionDeportiva, TipoMercadoDeportivo, EstadoInversionDeportiva

class DeportesService:
    def __init__(self, db: Session):
        self.db = db

    def crear_inversion(self, deporte: str, tipo_mercado: str, objetivo: str,
                        capital: float, ganancia_pot: float, perdida_pot: float,
                        cuota: float = None, notas: str = "") -> InversionDeportiva:
        # Validación y formateo de reglas
        tipo_enum = TipoMercadoDeportivo[tipo_mercado.upper()]
        
        if tipo_enum == TipoMercadoDeportivo.EQUIPO:
            objetivo_formateado = str(objetivo).strip().upper()
        elif tipo_enum == TipoMercadoDeportivo.RESULTADO:
            objetivo_formateado = str(objetivo).strip() # Acepta formatos como "2-1", "105", etc.
        else: # ESTADISTICA
            objetivo_formateado = str(objetivo).strip().upper() # Acepta "OVER 8.5 STRIKEOUTS", etc.

        inversion = InversionDeportiva(
            deporte=deporte.upper(),
            tipo_mercado=tipo_enum,
            objetivo=objetivo_formateado,
            capital_invertido=Decimal(str(capital)),
            ganancia_potencial=Decimal(str(ganancia_pot)),
            perdida_potencial=Decimal(str(perdida_pot)),
            estado=EstadoInversionDeportiva.ABIERTA,
            pnl_realizado=Decimal("0.00"),
            cuota_odds=Decimal(str(cuota)) if cuota else None,
            notas=notas
        )
        self.db.add(inversion)
        self.db.commit()
        self.db.refresh(inversion)
        return inversion

    def liquidar_inversion(self, inv_id: int, nuevo_estado: str) -> InversionDeportiva:
        inv = self.db.query(InversionDeportiva).filter_by(id=inv_id).first()
        if not inv:
            raise ValueError("Inversión no encontrada")
            
        estado_enum = EstadoInversionDeportiva[nuevo_estado.upper()]
        inv.estado = estado_enum
        inv.fecha_cierre = datetime.utcnow()
        
        if estado_enum == EstadoInversionDeportiva.GANADA:
            inv.pnl_realizado = inv.ganancia_potencial
        elif estado_enum == EstadoInversionDeportiva.PERDIDA:
            # Se registra como número negativo para la contabilidad
            inv.pnl_realizado = -abs(inv.perdida_potencial)
        else: # NULA o ABIERTA
            inv.pnl_realizado = Decimal("0.00")
            
        self.db.commit()
        self.db.refresh(inv)
        return inv

    def obtener_resumen_y_estadisticas(self) -> Dict[str, Any]:
        todas = self.db.query(InversionDeportiva).all()
        cerradas = [i for i in todas if i.estado in [EstadoInversionDeportiva.GANADA, EstadoInversionDeportiva.PERDIDA]]
        
        total_inversiones = len(todas)
        abiertas = len([i for i in todas if i.estado == EstadoInversionDeportiva.ABIERTA])
        ganadas = len([i for i in todas if i.estado == EstadoInversionDeportiva.GANADA])
        perdidas = len([i for i in todas if i.estado == EstadoInversionDeportiva.PERDIDA])
        
        capital_en_juego = sum(float(i.capital_invertido) for i in todas if i.estado == EstadoInversionDeportiva.ABIERTA)
        capital_total_hist = sum(float(i.capital_invertido) for i in todas)
        pnl_neto = sum(float(i.pnl_realizado) for i in cerradas)
        
        win_rate = (ganadas / len(cerradas) * 100) if cerradas else 0.0

        # Análisis por Equipo / Objetivo (Quién genera más ganancias y cuántas veces se invirtió)
        stats_objetivos = {}
        for idx in cerradas:
            obj = idx.objetivo
            if obj not in stats_objetivos:
                stats_objetivos[obj] = {"veces": 0, "pnl": 0.0, "ganadas": 0, "perdidas": 0, "deporte": idx.deporte}
            
            stats_objetivos[obj]["veces"] += 1
            stats_objetivos[obj]["pnl"] += float(idx.pnl_realizado)
            if idx.estado == EstadoInversionDeportiva.GANADA:
                stats_objetivos[obj]["ganadas"] += 1
            elif idx.estado == EstadoInversionDeportiva.PERDIDA:
                stats_objetivos[obj]["perdidas"] += 1

        top_objetivos = sorted(stats_objetivos.items(), key=lambda x: x[1]["pnl"], reverse=True)
        equipo_mas_rentable = top_objetivos[0] if top_objetivos else ("Ninguno", {"pnl": 0.0, "veces": 0})

        return {
            "total_inversiones": total_inversiones,
            "abiertas": abiertas,
            "ganadas": ganadas,
            "perdidas": perdidas,
            "win_rate": round(win_rate, 1),
            "capital_en_juego": round(capital_en_juego, 2),
            "capital_total_historico": round(capital_total_hist, 2),
            "pnl_neto": round(pnl_neto, 2),
            "equipo_mas_rentable": equipo_mas_rentable[0],
            "max_ganancia_equipo": round(equipo_mas_rentable[1]["pnl"], 2),
            "desglose_por_objetivo": [
                {"objetivo": k, **v} for k, v in stats_objetivos.items()
            ]
        }

    def obtener_reporte_por_fechas(self, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, Any]:
        """
        Filtra las inversiones cerradas por fecha de cierre y devuelve las estadísticas.
        """
        inversiones = self.db.query(InversionDeportiva).filter(
            InversionDeportiva.estado.in_([EstadoInversionDeportiva.GANADA, EstadoInversionDeportiva.PERDIDA]),
            InversionDeportiva.fecha_cierre >= fecha_inicio,
            InversionDeportiva.fecha_cierre <= fecha_fin
        ).all()

        ganadas = len([i for i in inversiones if i.estado == EstadoInversionDeportiva.GANADA])
        perdidas = len([i for i in inversiones if i.estado == EstadoInversionDeportiva.PERDIDA])
        pnl_total = sum(float(i.pnl_realizado) for i in inversiones)

        return {
            "ganadas": ganadas,
            "perdidas": perdidas,
            "pnl_total": round(pnl_total, 2),
            "total_inversiones": len(inversiones)
        }