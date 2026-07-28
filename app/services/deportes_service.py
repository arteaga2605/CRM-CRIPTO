from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional

from app.models import InversionDeportiva, TipoMercadoDeportivo, EstadoInversionDeportiva, RetiroDeportivo, InyeccionCapitalDeportivo

class DeportesService:
    def __init__(self, db: Session):
        self.db = db

    def crear_inversion(self, deporte: str, tipo_mercado: str, objetivo: str,
                        capital: float, ganancia_pot: float, perdida_pot: float,
                        notas: str = "") -> InversionDeportiva:
        tipo_enum = TipoMercadoDeportivo[tipo_mercado.upper()]

        if tipo_enum == TipoMercadoDeportivo.EQUIPO:
            objetivo_formateado = str(objetivo).strip().upper()
        elif tipo_enum == TipoMercadoDeportivo.RESULTADO:
            objetivo_formateado = str(objetivo).strip()
        else:
            objetivo_formateado = str(objetivo).strip().upper()

        ganancia_neta = Decimal(str(ganancia_pot)) - Decimal(str(capital))

        inversion = InversionDeportiva(
            deporte=deporte.upper(),
            tipo_mercado=tipo_enum,
            objetivo=objetivo_formateado,
            capital_invertido=Decimal(str(capital)),
            ganancia_potencial=ganancia_neta,
            perdida_potencial=Decimal(str(perdida_pot)),
            estado=EstadoInversionDeportiva.ABIERTA,
            pnl_realizado=Decimal("0.00"),
            cuota_odds=None,
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
            inv.pnl_realizado = -abs(inv.perdida_potencial)
        else:
            inv.pnl_realizado = Decimal("0.00")

        self.db.commit()
        self.db.refresh(inv)
        return inv

    # ─── RETIROS ───
    def registrar_retiro(self, monto: float, notas: str = "") -> RetiroDeportivo:
        if monto <= 0:
            raise ValueError("El monto del retiro debe ser mayor a cero")

        capital_disponible = self._calcular_capital_actual()
        if monto > capital_disponible:
            raise ValueError(f"Capital insuficiente. Disponible: ${capital_disponible:.2f}, Solicitado: ${monto:.2f}")

        retiro = RetiroDeportivo(
            monto=Decimal(str(monto)),
            notas=notas
        )
        self.db.add(retiro)
        self.db.commit()
        self.db.refresh(retiro)
        return retiro

    def obtener_total_retiros(self) -> float:
        total = self.db.query(func.sum(RetiroDeportivo.monto)).scalar()
        return float(total or 0.0)

    def obtener_historial_retiros(self, limit: int = 50) -> List[RetiroDeportivo]:
        return self.db.query(RetiroDeportivo).order_by(RetiroDeportivo.fecha_retiro.desc()).limit(limit).all()

    # ─── INYECCIONES DE CAPITAL (NUEVO) ───
    def registrar_inyeccion(self, monto: float, notas: str = "") -> InyeccionCapitalDeportivo:
        if monto <= 0:
            raise ValueError("El monto de la inyección debe ser mayor a cero")

        inyeccion = InyeccionCapitalDeportivo(
            monto=Decimal(str(monto)),
            notas=notas
        )
        self.db.add(inyeccion)
        self.db.commit()
        self.db.refresh(inyeccion)
        return inyeccion

    def obtener_total_inyecciones(self) -> float:
        total = self.db.query(func.sum(InyeccionCapitalDeportivo.monto)).scalar()
        return float(total or 0.0)

    def obtener_historial_inyecciones(self, limit: int = 50) -> List[InyeccionCapitalDeportivo]:
        return self.db.query(InyeccionCapitalDeportivo).order_by(InyeccionCapitalDeportivo.fecha_inyeccion.desc()).limit(limit).all()

    def _calcular_capital_actual(self, capital_base: float = 1000.00) -> float:
        """Calcula el capital real disponible considerando base, inyecciones, PnL y retiros."""
        stats = self.obtener_resumen_y_estadisticas(capital_base=capital_base)
        return stats["capital_actual"]

    def pnl_diario(self, dias: int = 7) -> List[Dict[str, Any]]:
        """Devuelve el PnL realizado agrupado por día de cierre (últimos N días)."""
        desde = datetime.utcnow() - timedelta(days=dias)
        resultados = self.db.query(
            func.date(InversionDeportiva.fecha_cierre).label("fecha"),
            func.sum(InversionDeportiva.pnl_realizado).label("pnl")
        ).filter(
            InversionDeportiva.estado.in_([
                EstadoInversionDeportiva.GANADA,
                EstadoInversionDeportiva.PERDIDA
            ]),
            InversionDeportiva.fecha_cierre >= desde
        ).group_by(func.date(InversionDeportiva.fecha_cierre)).order_by("fecha").all()

        pnl_por_dia = {str(r.fecha): float(r.pnl or 0) for r in resultados}
        hoy = datetime.utcnow().date()
        datos_finales = []
        for i in range(dias - 1, -1, -1):
            fecha = hoy - timedelta(days=i)
            fecha_str = fecha.strftime("%Y-%m-%d")
            datos_finales.append({
                "fecha": fecha_str,
                "pnl": pnl_por_dia.get(fecha_str, 0.0)
            })
        return datos_finales

    def obtener_resumen_y_estadisticas(self, capital_base: float = 1000.00) -> Dict[str, Any]:
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

        total_retiros = self.obtener_total_retiros()
        total_inyecciones = self.obtener_total_inyecciones()
        capital_actual = capital_base + total_inyecciones + pnl_neto - total_retiros

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

        ultimas_10 = cerradas[-10:] if len(cerradas) >= 10 else cerradas
        datos_ultimas_10 = [
            {
                "id": idx.id,
                "objetivo": idx.objetivo,
                "pnl": float(idx.pnl_realizado),
                "estado": idx.estado.value,
                "deporte": idx.deporte
            }
            for idx in ultimas_10
        ]

        return {
            "total_inversiones": total_inversiones,
            "abiertas": abiertas,
            "ganadas": ganadas,
            "perdidas": perdidas,
            "win_rate": round(win_rate, 1),
            "capital_en_juego": round(capital_en_juego, 2),
            "capital_total_historico": round(capital_total_hist, 2),
            "pnl_neto": round(pnl_neto, 2),
            "total_retiros": round(total_retiros, 2),
            "total_inyecciones": round(total_inyecciones, 2),
            "capital_actual": round(capital_actual, 2),
            "equipo_mas_rentable": equipo_mas_rentable[0],
            "max_ganancia_equipo": round(equipo_mas_rentable[1]["pnl"], 2),
            "desglose_por_objetivo": [
                {"objetivo": k, **v} for k, v in stats_objetivos.items()
            ],
            "ultimas_10_inversiones": datos_ultimas_10
        }

    def obtener_reporte_por_fechas(self, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, Any]:
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
