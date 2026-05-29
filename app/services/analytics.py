"""
Modulo de analytics para el CRM Crypto.
Genera reportes, metricas y insights.
"""
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from decimal import Decimal

from app.models import ClienteCripto, Interaccion, Oportunidad, Tarea, TipoInteraccion

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def rendimiento_por_categoria(self) -> List[Dict]:
        result = self.db.query(
            ClienteCripto.categoria,
            func.count(ClienteCripto.id).label('count'),
            func.avg(ClienteCripto.roi_porcentaje).label('avg_roi'),
            func.sum(ClienteCripto.pnl_total).label('total_pnl')
        ).group_by(ClienteCripto.categoria).all()

        return [
            {
                "categoria": r.categoria,
                "monedas": r.count,
                "roi_promedio": round(float(r.avg_roi or 0), 2),
                "pnl_total": round(float(r.total_pnl or 0), 2)
            }
            for r in result
        ]

    def evolucion_pnl_mensual(self, meses: int = 6) -> List[Dict]:
        desde = datetime.utcnow() - timedelta(days=meses*30)
        result = self.db.query(
            func.strftime('%Y-%m', Interaccion.timestamp).label('mes'),
            func.sum(Interaccion.pnl_realizado).label('pnl')
        ).filter(
            Interaccion.timestamp >= desde,
            Interaccion.tipo == TipoInteraccion.VENTA
        ).group_by('mes').order_by('mes').all()

        return [
            {"mes": r.mes, "pnl_realizado": round(float(r.pnl or 0), 2)}
            for r in result
        ]

    def metricas_oportunidades(self) -> Dict:
        total = self.db.query(Oportunidad).count()
        abiertas = self.db.query(Oportunidad).filter_by(estado="abierta").count()
        ejecutadas = self.db.query(Oportunidad).filter_by(estado="ejecutada").count()
        canceladas = self.db.query(Oportunidad).filter_by(estado="cancelada").count()
        pnl_opps = self.db.query(func.sum(Oportunidad.resultado_pnl)).filter(
            Oportunidad.estado == "ejecutada"
        ).scalar()
        avg_rr = self.db.query(func.avg(Oportunidad.riesgo_beneficio)).filter(
            Oportunidad.estado == "ejecutada"
        ).scalar()

        return {
            "total_oportunidades": total,
            "abiertas": abiertas,
            "ejecutadas": ejecutadas,
            "canceladas": canceladas,
            "tasa_ejecucion": round(ejecutadas / total * 100, 1) if total > 0 else 0,
            "pnl_total_oportunidades": round(float(pnl_opps or 0), 2),
            "riesgo_beneficio_promedio": round(float(avg_rr or 0), 2)
        }

    def eficiencia_tareas(self, dias: int = 30) -> Dict:
        desde = datetime.utcnow() - timedelta(days=dias)
        total = self.db.query(Tarea).filter(Tarea.fecha_creacion >= desde).count()
        completadas = self.db.query(Tarea).filter(
            Tarea.completada == True,
            Tarea.fecha_creacion >= desde
        ).count()
        return {
            "tareas_creadas": total,
            "tareas_completadas": completadas,
            "tasa_completitud": round(completadas / total * 100, 1) if total > 0 else 0,
            "periodo_dias": dias
        }

    def distribucion_portafolio(self) -> List[Dict]:
        clientes = self.db.query(ClienteCripto).filter(
            ClienteCripto.cantidad_total > 0
        ).all()
        total_valor = sum(float(c.valor_mercado) for c in clientes)
        return [
            {
                "symbol": c.symbol,
                "valor": round(float(c.valor_mercado), 2),
                "porcentaje": round(float(c.valor_mercado) / total_valor * 100, 2) if total_valor > 0 else 0,
                "roi": round(float(c.roi_porcentaje), 2)
            }
            for c in sorted(clientes, key=lambda x: float(x.valor_mercado), reverse=True)
        ]

    def alertas_inteligentes(self) -> List[Dict]:
        alertas = []
        peligro = self.db.query(ClienteCripto).filter(
            ClienteCripto.roi_porcentaje < -20,
            ClienteCripto.cantidad_total > 0
        ).all()
        for c in peligro:
            alertas.append({
                "nivel": "CRITICO",
                "tipo": "perdida_excesiva",
                "symbol": c.symbol,
                "mensaje": f"{c.symbol} con perdida del {float(c.roi_porcentaje):.1f}%. Considerar stop o promediar.",
                "accion_sugerida": "revisar_stop_loss"
            })
        vip = self.db.query(ClienteCripto).filter(
            ClienteCripto.roi_porcentaje > 50,
            ClienteCripto.cantidad_total > 0
        ).all()
        for c in vip:
            alertas.append({
                "nivel": "INFO",
                "tipo": "take_profit_sugerido",
                "symbol": c.symbol,
                "mensaje": f"{c.symbol} ganando {float(c.roi_porcentaje):.1f}%. Considerar venta parcial.",
                "accion_sugerida": "vender_50_porciento"
            })
        dist = self.distribucion_portafolio()
        if dist:
            max_pos = dist[0]
            if max_pos["porcentaje"] > 30:
                alertas.append({
                    "nivel": "ADVERTENCIA",
                    "tipo": "concentracion_alta",
                    "symbol": max_pos["symbol"],
                    "mensaje": f"{max_pos['symbol']} representa {max_pos['porcentaje']}% del portafolio. Diversificar.",
                    "accion_sugerida": "rebalancear"
                })
        desde = datetime.utcnow() - timedelta(days=30)
        dormidos = self.db.query(ClienteCripto).filter(
            ClienteCripto.fecha_ultimo_contacto < desde,
            ClienteCripto.cantidad_total > 0
        ).all()
        for c in dormidos:
            alertas.append({
                "nivel": "BAJO",
                "tipo": "cliente_dormido",
                "symbol": c.symbol,
                "mensaje": f"{c.symbol} sin movimiento en 30+ dias. Revisar si mantener.",
                "accion_sugerida": "revision_estrategia"
            })
        return alertas

    def daily_pnl(self, days: int = 7) -> List[Dict]:
        """
        Retorna el PnL realizado por día (solo ventas) para los últimos 'days' días.
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        # Agrupar por día (fecha sin hora)
        results = self.db.query(
            func.date(Interaccion.timestamp).label('date'),
            func.sum(Interaccion.pnl_realizado).label('total_pnl')
        ).filter(
            Interaccion.tipo == TipoInteraccion.VENTA,
            Interaccion.timestamp >= start_date
        ).group_by(func.date(Interaccion.timestamp)).order_by(func.date(Interaccion.timestamp)).all()
        
        # Llenar los días que no tienen datos con 0
        daily_data = {}
        for r in results:
            daily_data[r.date] = float(r.total_pnl)
        
        # Crear lista de los últimos 'days' días (incluyendo hoy)
        today = datetime.utcnow().date()
        pnl_list = []
        for i in range(days - 1, -1, -1):
            date = today - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            pnl = daily_data.get(date_str, 0.0)
            pnl_list.append({
                "date": date_str,
                "pnl": pnl
            })
        return pnl_list