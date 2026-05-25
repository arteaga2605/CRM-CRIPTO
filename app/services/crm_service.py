from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from decimal import Decimal

from app.models import (
    ClienteCripto, Interaccion, Oportunidad, Tarea,
    EstadoCliente, TipoInteraccion, init_db, SessionLocal
)

class CRMService:
    def __init__(self, db: Session):
        self.db = db
    
    # ═══════════════════════════════════════
    # GESTION DE CLIENTES (CRIPTO)
    # ═══════════════════════════════════════
    
    def registrar_cliente(self, symbol: str, nombre: str = None, 
                          categoria: str = "desconocida", **kwargs) -> ClienteCripto:
        """Dar de alta una nueva criptomoneda en el CRM"""
        symbol = symbol.upper()
        existente = self.db.query(ClienteCripto).filter_by(symbol=symbol).first()
        if existente:
            raise ValueError(f"El cliente {symbol} ya existe en el CRM")
        
        cliente = ClienteCripto(
            symbol=symbol,
            nombre=nombre or symbol,
            categoria=categoria,
            **kwargs
        )
        self.db.add(cliente)
        self.db.commit()
        self.db.refresh(cliente)
        return cliente
    
    def obtener_cliente(self, symbol: str) -> Optional[ClienteCripto]:
        return self.db.query(ClienteCripto).filter_by(symbol=symbol.upper()).first()
    
    def listar_clientes(self, estado: str = None, categoria: str = None,
                        min_roi: float = None, tags: str = None) -> List[ClienteCripto]:
        query = self.db.query(ClienteCripto)
        if estado:
            query = query.filter(ClienteCripto.estado == estado)
        if categoria:
            query = query.filter(ClienteCripto.categoria == categoria)
        if min_roi is not None:
            query = query.filter(ClienteCripto.roi_porcentaje >= min_roi)
        if tags:
            query = query.filter(ClienteCripto.tags.contains(tags))
        return query.order_by(ClienteCripto.prioridad).all()
    
    def actualizar_estado_cliente(self, symbol: str) -> Optional[ClienteCripto]:
        """Recalcula el estado emocional/estrategico de la moneda"""
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            return None
        
        roi = float(cliente.roi_porcentaje) if cliente.roi_porcentaje else 0
        cantidad = float(cliente.cantidad_total) if cliente.cantidad_total else 0
        
        if cantidad == 0:
            nuevo_estado = EstadoCliente.PROSPECTO
        elif roi > 50:
            nuevo_estado = EstadoCliente.VIP
        elif roi < -20:
            nuevo_estado = EstadoCliente.ACTIVO_PELIGRO
        elif roi == 0 and cantidad > 0:
            nuevo_estado = EstadoCliente.DORMANTE
        elif roi > 0:
            nuevo_estado = EstadoCliente.ACTIVO_COMPRA
        else:
            nuevo_estado = EstadoCliente.ACTIVO_PELIGRO
        
        cliente.estado = nuevo_estado
        self.db.commit()
        return cliente
    
    def actualizar_precio_mercado(self, symbol: str, precio: float) -> ClienteCripto:
        """Actualiza precio actual y recalcula metricas de mercado"""
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            raise ValueError(f"Cliente {symbol} no encontrado")
        
        cliente.precio_actual = Decimal(str(precio))
        cantidad = float(cliente.cantidad_total)
        
        if cantidad > 0:
            cliente.valor_mercado = Decimal(str(precio * cantidad))
            costo_total = float(cliente.cantidad_total) * float(cliente.costo_promedio)
            if costo_total > 0:
                cliente.pnl_total = cliente.valor_mercado - Decimal(str(costo_total))
                cliente.roi_porcentaje = (cliente.pnl_total / Decimal(str(costo_total))) * 100
        
        self.db.commit()
        self.actualizar_estado_cliente(symbol)
        return cliente
    
    # ═══════════════════════════════════════
    # INTERACCIONES (TRANSACCIONES)
    # ═══════════════════════════════════════
    
    def registrar_interaccion(self, symbol: str, tipo: str,
                              cantidad: float, precio: float,
                              fee: float = 0.0, exchange: str = "binance",
                              notas: str = "") -> Interaccion:
        """Registra compra, venta, staking... como interaccion con el cliente"""
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            raise ValueError(f"Criptomoneda {symbol} no registrada. Creala primero.")
        
        tipo_enum = TipoInteraccion(tipo)
        monto = cantidad * precio
        
        interaccion = Interaccion(
            cliente_id=cliente.id,
            tipo=tipo_enum,
            cantidad=Decimal(str(cantidad)),
            precio_unitario=Decimal(str(precio)),
            monto_usd=Decimal(str(monto)),
            fee=Decimal(str(fee)),
            exchange=exchange,
            notas=notas
        )
        
        # Actualizar metricas del cliente
        self._recalcular_metricas_post_interaccion(cliente, interaccion)
        
        self.db.add(interaccion)
        self.db.commit()
        self.db.refresh(interaccion)
        return interaccion
    
    def _recalcular_metricas_post_interaccion(self, cliente: ClienteCripto, 
                                               interaccion: Interaccion):
        cantidad = float(interaccion.cantidad)
        precio = float(interaccion.precio_unitario)
        tipo = interaccion.tipo
        
        if tipo == TipoInteraccion.COMPRA:
            total_previo = float(cliente.cantidad_total) * float(cliente.costo_promedio)
            total_nuevo = cantidad * precio
            nueva_cantidad = float(cliente.cantidad_total) + cantidad
            if nueva_cantidad > 0:
                cliente.costo_promedio = Decimal(str((total_previo + total_nuevo) / nueva_cantidad))
            cliente.cantidad_total = Decimal(str(nueva_cantidad))
            cliente.inversion_total += Decimal(str(cantidad * precio))
            
        elif tipo == TipoInteraccion.VENTA:
            pnl = (precio - float(cliente.costo_promedio)) * cantidad
            interaccion.pnl_realizado = Decimal(str(pnl))
            nueva_cantidad = float(cliente.cantidad_total) - cantidad
            cliente.cantidad_total = Decimal(str(max(0, nueva_cantidad)))
            cliente.pnl_total += Decimal(str(pnl))
            if nueva_cantidad <= 0:
                cliente.costo_promedio = Decimal("0")
                cliente.estado = EstadoCliente.CHURN
                
        elif tipo == TipoInteraccion.STAKING:
            # Staking no afecta cantidad total, es solo un cambio de estado
            pass
            
        elif tipo == TipoInteraccion.DIVIDENDO or tipo == TipoInteraccion.AIRDROP:
            cliente.cantidad_total += Decimal(str(cantidad))
            # Costo promedio se mantiene, es ganancia "gratis"
    
    def historial_interacciones(self, symbol: str) -> List[Interaccion]:
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            return []
        return self.db.query(Interaccion).filter_by(cliente_id=cliente.id)\
                   .order_by(Interaccion.timestamp.desc()).all()
    
    # ═══════════════════════════════════════
    # OPORTUNIDADES (PIPELINE DE TRADES)
    # ═══════════════════════════════════════
    
    def crear_oportunidad(self, symbol: str, tipo: str,
                          entrada: float, objetivo: float, stop: float,
                          monto_planificado: float = 0,
                          confianza: int = 3, notas: str = "") -> Oportunidad:
        """Crea un trade setup en el pipeline"""
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            raise ValueError(f"Cliente {symbol} no existe")
        
        riesgo = abs(entrada - stop)
        beneficio = abs(objetivo - entrada)
        rb = beneficio / riesgo if riesgo > 0 else 0
        
        opp = Oportunidad(
            cliente_id=cliente.id,
            tipo=tipo,
            precio_entrada=Decimal(str(entrada)),
            precio_objetivo=Decimal(str(objetivo)),
            precio_stop_loss=Decimal(str(stop)),
            riesgo_beneficio=Decimal(str(round(rb, 2))),
            monto_planificado=Decimal(str(monto_planificado)),
            confianza=confianza,
            notas_analisis=notas
        )
        self.db.add(opp)
        self.db.commit()
        self.db.refresh(opp)
        return opp
    
    def cerrar_oportunidad(self, opp_id: int, estado: str, pnl: float = None):
        opp = self.db.query(Oportunidad).filter_by(id=opp_id).first()
        if not opp:
            raise ValueError("Oportunidad no encontrada")
        opp.estado = estado
        opp.fecha_ejecucion = datetime.utcnow()
        if pnl is not None:
            opp.resultado_pnl = Decimal(str(pnl))
        self.db.commit()
        return opp
    
    def oportunidades_por_estado(self, estado: str = "abierta") -> List[Oportunidad]:
        return self.db.query(Oportunidad).filter_by(estado=estado)\
                   .order_by(Oportunidad.confianza.desc()).all()
    
    # ═══════════════════════════════════════
    # TAREAS Y ALERTAS
    # ═══════════════════════════════════════
    
    def crear_tarea(self, symbol: str, tipo: str, descripcion: str,
                    dias: int = 1, prioridad: int = 2) -> Tarea:
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            raise ValueError(f"Cliente {symbol} no existe")
        
        tarea = Tarea(
            cliente_id=cliente.id,
            tipo_tarea=tipo,
            descripcion=descripcion,
            fecha_limite=datetime.utcnow() + timedelta(days=dias),
            prioridad=prioridad
        )
        self.db.add(tarea)
        self.db.commit()
        self.db.refresh(tarea)
        return tarea
    
    def completar_tarea(self, tarea_id: int) -> Tarea:
        tarea = self.db.query(Tarea).filter_by(id=tarea_id).first()
        if not tarea:
            raise ValueError("Tarea no encontrada")
        tarea.completada = True
        tarea.fecha_completada = datetime.utcnow()
        self.db.commit()
        return tarea
    
    def tareas_pendientes(self, urgentes: bool = False) -> List[Tarea]:
        query = self.db.query(Tarea).filter(
            Tarea.completada == False,
            Tarea.fecha_limite <= datetime.utcnow()
        )
        if urgentes:
            query = query.filter(Tarea.prioridad == 1)
        return query.order_by(Tarea.fecha_limite).all()
    
    def tareas_proximas(self, dias: int = 3) -> List[Tarea]:
        limite = datetime.utcnow() + timedelta(days=dias)
        return self.db.query(Tarea).filter(
            Tarea.completada == False,
            Tarea.fecha_limite <= limite
        ).order_by(Tarea.fecha_limite).all()
    
    # ═══════════════════════════════════════
    # ANALYTICS & REPORTES
    # ═══════════════════════════════════════
    
    def resumen_portafolio(self) -> dict:
        clientes = self.db.query(ClienteCripto).all()
        interacciones = self.db.query(Interaccion).count()
        oportunidades_abiertas = self.db.query(Oportunidad).filter_by(estado="abierta").count()
        tareas_pend = len(self.tareas_pendientes())
        
        total_invertido = sum(float(c.inversion_total) for c in clientes)
        total_valor = sum(float(c.valor_mercado) for c in clientes)
        pnl_total = total_valor - total_invertido
        roi = (pnl_total / total_invertido * 100) if total_invertido > 0 else 0
        
        return {
            "total_clientes": len(clientes),
            "clientes_activos": len([c for c in clientes if float(c.cantidad_total) > 0]),
            "clientes_vip": len([c for c in clientes if c.estado == EstadoCliente.VIP]),
            "clientes_peligro": len([c for c in clientes if c.estado == EstadoCliente.ACTIVO_PELIGRO]),
            "total_invertido": round(total_invertido, 2),
            "total_valor_mercado": round(total_valor, 2),
            "pnl_total": round(pnl_total, 2),
            "roi_porcentaje": round(roi, 2),
            "total_interacciones": interacciones,
            "oportunidades_abiertas": oportunidades_abiertas,
            "tareas_pendientes": tareas_pend
        }
    
    def top_performers(self, limit: int = 5) -> List[ClienteCripto]:
        return self.db.query(ClienteCripto)\
                   .filter(ClienteCripto.roi_porcentaje > 0)\
                   .order_by(ClienteCripto.roi_porcentaje.desc())\
                   .limit(limit).all()
    
    def peores_performers(self, limit: int = 5) -> List[ClienteCripto]:
        return self.db.query(ClienteCripto)\
                   .filter(ClienteCripto.roi_porcentaje < 0)\
                   .order_by(ClienteCripto.roi_porcentaje.asc())\
                   .limit(limit).all()
    
    def clientes_dormidos(self, dias: int = 30) -> List[ClienteCripto]:
        limite = datetime.utcnow() - timedelta(days=dias)
        return self.db.query(ClienteCripto).filter(
            ClienteCripto.fecha_ultimo_contacto < limite,
            ClienteCripto.cantidad_total > 0
        ).all()