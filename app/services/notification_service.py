"""
Servicio para generar y gestionar notificaciones push.
"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Any
from decimal import Decimal

from app.models import Notification, ClienteCripto, Oportunidad, Tarea
from app.services.crm_service import CRMService
from app.services.exchange_sync import ExchangeConnector

class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.connector = ExchangeConnector()
        self.crm = CRMService(db)

    def create_notification(self, message: str, notif_type: str, related_id: int = None) -> Notification:
        """Crea una nueva notificación en la base de datos."""
        notif = Notification(
            message=message,
            type=notif_type,
            related_id=related_id,
            is_read=False
        )
        self.db.add(notif)
        self.db.commit()
        self.db.refresh(notif)
        return notif

    def get_unread_notifications(self, limit: int = 20) -> List[Notification]:
        """Obtiene las notificaciones no leídas, ordenadas por fecha descendente."""
        return self.db.query(Notification)\
            .filter(Notification.is_read == False)\
            .order_by(Notification.created_at.desc())\
            .limit(limit).all()

    def get_recent_notifications(self, limit: int = 20) -> List[Notification]:
        """Obtiene las últimas notificaciones (leídas y no leídas)."""
        return self.db.query(Notification)\
            .order_by(Notification.created_at.desc())\
            .limit(limit).all()

    def mark_as_read(self, notif_id: int) -> bool:
        notif = self.db.query(Notification).filter_by(id=notif_id).first()
        if notif:
            notif.is_read = True
            self.db.commit()
            return True
        return False

    def mark_all_as_read(self):
        self.db.query(Notification).update({Notification.is_read: True})
        self.db.commit()

    def check_price_alerts(self) -> int:
        """Verifica cambios de precio superiores al 5% y genera notificaciones."""
        clientes = self.db.query(ClienteCripto).filter(ClienteCripto.cantidad_total > 0).all()
        alerts_count = 0
        for cliente in clientes:
            precio_actual = self.connector.obtener_precio(cliente.symbol)
            if precio_actual == 0:
                continue
            precio_anterior = float(cliente.precio_actual)
            if precio_anterior == 0:
                self.crm.actualizar_precio_mercado(cliente.symbol, precio_actual)
                continue
            cambio = abs((precio_actual - precio_anterior) / precio_anterior) * 100
            if cambio >= 5:
                direccion = "subido" if precio_actual > precio_anterior else "bajado"
                message = f"💰 {cliente.symbol} ha {direccion} un {cambio:.1f}% (${precio_anterior:.2f} → ${precio_actual:.2f})"
                self.create_notification(message, "price_alert", cliente.id)
                alerts_count += 1
            self.crm.actualizar_precio_mercado(cliente.symbol, precio_actual)
        return alerts_count

    def check_market_trend_change(self) -> int:
        ticker = self.connector.obtener_ticker("BTC")
        change_24h = ticker.get("percentage", 0.0)
        if change_24h > 1:
            current_trend = "alcista"
        elif change_24h < -1:
            current_trend = "bajista"
        else:
            current_trend = "neutral"
        last_trend_notif = self.db.query(Notification)\
            .filter(Notification.type == "trend_change")\
            .order_by(Notification.created_at.desc())\
            .first()
        last_trend = "neutral"
        if last_trend_notif:
            last_trend = "alcista" if "alcista" in last_trend_notif.message else "bajista" if "bajista" in last_trend_notif.message else "neutral"
        if current_trend != last_trend:
            message = f"📈 Cambio de tendencia del mercado: BTC ahora en tendencia {current_trend.upper()} (cambio 24h: {change_24h:.1f}%)"
            self.create_notification(message, "trend_change")
            return 1
        return 0

    def check_opportunities_alerts(self) -> int:
        oportunidades = self.db.query(Oportunidad).filter(Oportunidad.estado == "abierta").all()
        alerts_count = 0
        for opp in oportunidades:
            cliente = opp.cliente
            if not cliente:
                continue
            precio_actual = float(cliente.precio_actual)
            precio_objetivo = float(opp.precio_objetivo)
            precio_stop = float(opp.precio_stop_loss)
            if precio_actual >= precio_objetivo:
                message = f"🎯 ¡Objetivo alcanzado! {cliente.symbol} llegó a ${precio_actual:.2f} (objetivo: ${precio_objetivo:.2f})"
                self.create_notification(message, "opportunity_alert", opp.id)
                alerts_count += 1
            elif precio_actual <= precio_stop:
                message = f"🛑 Stop loss activado en {cliente.symbol} (precio: ${precio_actual:.2f}, stop: ${precio_stop:.2f})"
                self.create_notification(message, "opportunity_alert", opp.id)
                alerts_count += 1
        return alerts_count

    def check_task_reminders(self) -> int:
        ahora = datetime.utcnow()
        limite = ahora + timedelta(days=1)
        tareas = self.db.query(Tarea).filter(
            Tarea.completada == False,
            Tarea.fecha_limite <= limite,
            Tarea.fecha_limite > ahora
        ).all()
        alerts_count = 0
        for tarea in tareas:
            cliente = tarea.cliente
            message = f"⏰ Recordatorio: La tarea '{tarea.tipo_tarea}' para {cliente.symbol} vence en {(tarea.fecha_limite - ahora).seconds // 3600} horas."
            self.create_notification(message, "task_reminder", tarea.id)
            alerts_count += 1
        return alerts_count

    def generate_all_alerts(self) -> Dict[str, int]:
        return {
            "price_alerts": self.check_price_alerts(),
            "trend_change": self.check_market_trend_change(),
            "opportunity_alerts": self.check_opportunities_alerts(),
            "task_reminders": self.check_task_reminders()
        }