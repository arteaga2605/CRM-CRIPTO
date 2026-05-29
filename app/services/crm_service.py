from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from decimal import Decimal

from app.models import (
    ClienteCripto, Interaccion, Oportunidad, Tarea, LoteCompra,
    EstadoCliente, TipoInteraccion, TipoOportunidad
)

class CRMService:
    def __init__(self, db: Session):
        self.db = db

    # ═══════════════════════════════════════
    # GESTION DE CLIENTES (CRIPTO)
    # ═══════════════════════════════════════

    def registrar_cliente(self, symbol: str, nombre: str = None, 
                          categoria: str = "desconocida", **kwargs) -> ClienteCripto:
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
    # INTERACCIONES CON FIFO Y COMISIONES
    # ═══════════════════════════════════════

    def registrar_compra(self, symbol: str, cantidad: float, precio: float,
                         fee: float = 0.0, exchange: str = "binance", notas: str = "") -> Dict[str, Any]:
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            raise ValueError(f"Criptomoneda {symbol} no registrada")

        costo_total = cantidad * precio + fee
        precio_con_fee = costo_total / cantidad

        lote = LoteCompra(
            cliente_id=cliente.id,
            cantidad=Decimal(str(cantidad)),
            cantidad_restante=Decimal(str(cantidad)),
            precio_unitario=Decimal(str(precio_con_fee)),
            exchange=exchange,
            notas=notas
        )
        self.db.add(lote)

        monto = cantidad * precio
        interaccion = Interaccion(
            cliente_id=cliente.id,
            tipo=TipoInteraccion.COMPRA,
            cantidad=Decimal(str(cantidad)),
            precio_unitario=Decimal(str(precio)),
            monto_usd=Decimal(str(monto)),
            fee=Decimal(str(fee)),
            exchange=exchange,
            notas=notas
        )
        self.db.add(interaccion)

        total_previo = float(cliente.cantidad_total) * float(cliente.costo_promedio)
        total_nuevo = costo_total
        nueva_cantidad = float(cliente.cantidad_total) + cantidad
        if nueva_cantidad > 0:
            cliente.costo_promedio = Decimal(str((total_previo + total_nuevo) / nueva_cantidad))
        cliente.cantidad_total = Decimal(str(nueva_cantidad))
        cliente.inversion_total += Decimal(str(costo_total))

        self.db.commit()
        self.db.refresh(lote)
        self.actualizar_estado_cliente(symbol)

        return {"lote": lote, "interaccion": interaccion}

    def registrar_venta_fifo(self, symbol: str, cantidad_vender: float, precio_venta: float,
                             fee: float = 0.0, exchange: str = "binance", notas: str = "") -> Dict[str, Any]:
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            raise ValueError(f"Cliente {symbol} no existe")

        cantidad_vender = Decimal(str(cantidad_vender))
        if cantidad_vender > cliente.cantidad_total:
            raise ValueError(f"No hay suficiente cantidad para vender. Disponible: {cliente.cantidad_total}")

        lotes = self.db.query(LoteCompra).filter(
            LoteCompra.cliente_id == cliente.id,
            LoteCompra.cantidad_restante > 0
        ).order_by(LoteCompra.fecha_compra.asc()).all()

        if not lotes:
            raise ValueError("No hay lotes de compra para este cliente")

        cantidad_a_vender = cantidad_vender
        pnl_total = Decimal("0")
        detalles_consumo = []

        for lote in lotes:
            if cantidad_a_vender <= 0:
                break
            disponible = lote.cantidad_restante
            a_consumir = min(disponible, cantidad_a_vender)

            precio_compra_con_fee = lote.precio_unitario
            precio_venta_dec = Decimal(str(precio_venta))
            pnl_lote = (precio_venta_dec - precio_compra_con_fee) * a_consumir
            pnl_total += pnl_lote

            lote.cantidad_restante -= a_consumir
            cantidad_a_vender -= a_consumir

            detalles_consumo.append({
                "lote_id": lote.id,
                "cantidad": float(a_consumir),
                "precio_compra": float(precio_compra_con_fee),
                "pnl_lote": float(pnl_lote)
            })

        pnl_total -= Decimal(str(fee))
        cantidad_vendida = cantidad_vender - cantidad_a_vender
        monto = float(cantidad_vendida) * precio_venta

        interaccion = Interaccion(
            cliente_id=cliente.id,
            tipo=TipoInteraccion.VENTA,
            cantidad=cantidad_vendida,
            precio_unitario=Decimal(str(precio_venta)),
            monto_usd=Decimal(str(monto)),
            fee=Decimal(str(fee)),
            exchange=exchange,
            notas=notas,
            pnl_realizado=pnl_total
        )
        self.db.add(interaccion)

        nueva_cantidad = cliente.cantidad_total - cantidad_vendida
        cliente.cantidad_total = nueva_cantidad
        cliente.pnl_total += pnl_total

        if nueva_cantidad > 0:
            lotes_restantes = self.db.query(LoteCompra).filter(
                LoteCompra.cliente_id == cliente.id,
                LoteCompra.cantidad_restante > 0
            ).all()
            inversion_restante = sum(float(l.cantidad_restante) * float(l.precio_unitario) for l in lotes_restantes)
            cliente.costo_promedio = Decimal(str(inversion_restante / float(nueva_cantidad))) if nueva_cantidad > 0 else Decimal("0")
        else:
            cliente.costo_promedio = Decimal("0")

        self.db.commit()
        self.actualizar_estado_cliente(symbol)

        return {
            "interaccion": interaccion,
            "pnl_total": float(pnl_total),
            "detalle_lotes": detalles_consumo
        }

    def registrar_interaccion_general(self, symbol: str, tipo: str, cantidad: float, precio: float,
                                      fee: float = 0.0, exchange: str = "binance", notas: str = ""):
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            raise ValueError(f"Cliente {symbol} no existe")
        interaccion = Interaccion(
            cliente_id=cliente.id,
            tipo=TipoInteraccion(tipo),
            cantidad=Decimal(str(cantidad)),
            precio_unitario=Decimal(str(precio)),
            monto_usd=Decimal(str(cantidad * precio)),
            fee=Decimal(str(fee)),
            exchange=exchange,
            notas=notas
        )
        self.db.add(interaccion)
        if tipo in ["staking", "airdrop", "dividendo"]:
            cliente.cantidad_total += Decimal(str(cantidad))
        self.db.commit()
        return {"interaccion": interaccion}

    def registrar_interaccion(self, symbol: str, tipo: str, cantidad: float, precio: float,
                              fee: float = 0.0, exchange: str = "binance", notas: str = ""):
        return self.registrar_interaccion_general(symbol, tipo, cantidad, precio, fee, exchange, notas)

    def eliminar_interaccion(self, interaccion_id: int) -> Dict[str, Any]:
        interaccion = self.db.query(Interaccion).filter_by(id=interaccion_id).first()
        if not interaccion:
            raise ValueError("Interacción no encontrada")

        cliente = interaccion.cliente
        symbol = cliente.symbol
        tipo_eliminado = interaccion.tipo.value
        cantidad_eliminada = float(interaccion.cantidad)

        self.db.delete(interaccion)
        self.db.commit()

        self.recalcular_cliente_desde_cero(symbol)

        return {
            "mensaje": f"Interacción {interaccion_id} de tipo {tipo_eliminado} eliminada",
            "cliente": symbol,
            "cantidad_afectada": cantidad_eliminada
        }

    def recalcular_cliente_desde_cero(self, symbol: str):
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            raise ValueError(f"Cliente {symbol} no encontrado")

        self.db.query(LoteCompra).filter(LoteCompra.cliente_id == cliente.id).delete()
        self.db.commit()

        cliente.cantidad_total = Decimal("0")
        cliente.costo_promedio = Decimal("0")
        cliente.inversion_total = Decimal("0")
        cliente.pnl_total = Decimal("0")
        cliente.valor_mercado = Decimal("0")
        cliente.roi_porcentaje = Decimal("0")
        self.db.commit()

        interacciones = self.db.query(Interaccion).filter(
            Interaccion.cliente_id == cliente.id
        ).order_by(Interaccion.timestamp.asc()).all()

        for inter in interacciones:
            tipo = inter.tipo.value
            cantidad = float(inter.cantidad)
            precio = float(inter.precio_unitario)
            fee = float(inter.fee)

            if tipo == "compra":
                costo_total = cantidad * precio + fee
                precio_con_fee = costo_total / cantidad

                lote = LoteCompra(
                    cliente_id=cliente.id,
                    cantidad=Decimal(str(cantidad)),
                    cantidad_restante=Decimal(str(cantidad)),
                    precio_unitario=Decimal(str(precio_con_fee)),
                    exchange=inter.exchange,
                    notas=inter.notas
                )
                self.db.add(lote)

                total_previo = float(cliente.cantidad_total) * float(cliente.costo_promedio)
                nueva_cantidad = float(cliente.cantidad_total) + cantidad
                if nueva_cantidad > 0:
                    cliente.costo_promedio = Decimal(str((total_previo + costo_total) / nueva_cantidad))
                cliente.cantidad_total = Decimal(str(nueva_cantidad))
                cliente.inversion_total += Decimal(str(costo_total))

            elif tipo == "venta":
                cantidad_vender = Decimal(str(cantidad))
                lotes = self.db.query(LoteCompra).filter(
                    LoteCompra.cliente_id == cliente.id,
                    LoteCompra.cantidad_restante > 0
                ).order_by(LoteCompra.fecha_compra.asc()).all()

                cantidad_a_vender = cantidad_vender
                pnl_total = Decimal("0")

                for lote in lotes:
                    if cantidad_a_vender <= 0:
                        break
                    disponible = lote.cantidad_restante
                    a_consumir = min(disponible, cantidad_a_vender)

                    pnl_lote = (Decimal(str(precio)) - lote.precio_unitario) * a_consumir
                    pnl_total += pnl_lote

                    lote.cantidad_restante -= a_consumir
                    cantidad_a_vender -= a_consumir

                pnl_total -= Decimal(str(fee))
                cantidad_vendida = cantidad_vender - cantidad_a_vender

                nueva_cantidad = float(cliente.cantidad_total) - float(cantidad_vendida)
                cliente.cantidad_total = Decimal(str(nueva_cantidad))
                cliente.pnl_total += pnl_total

                if nueva_cantidad > 0:
                    lotes_restantes = self.db.query(LoteCompra).filter(
                        LoteCompra.cliente_id == cliente.id,
                        LoteCompra.cantidad_restante > 0
                    ).all()
                    inversion_restante = sum(float(l.cantidad_restante) * float(l.precio_unitario) for l in lotes_restantes)
                    cliente.costo_promedio = Decimal(str(inversion_restante / nueva_cantidad))
                else:
                    cliente.costo_promedio = Decimal("0")

                inter.pnl_realizado = pnl_total

            else:
                if tipo in ["staking", "airdrop", "dividendo"]:
                    cliente.cantidad_total += Decimal(str(cantidad))

        if float(cliente.cantidad_total) > 0:
            precio_actual = float(cliente.precio_actual) if cliente.precio_actual else 0
            cliente.valor_mercado = Decimal(str(precio_actual * float(cliente.cantidad_total)))
            inversion_total = float(cliente.inversion_total)
            if inversion_total > 0:
                cliente.pnl_total = cliente.valor_mercado - Decimal(str(inversion_total))
                cliente.roi_porcentaje = (cliente.pnl_total / Decimal(str(inversion_total))) * 100

        self.db.commit()
        self.actualizar_estado_cliente(symbol)

    def historial_interacciones(self, symbol: str) -> List[Interaccion]:
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            return []
        return self.db.query(Interaccion).filter_by(cliente_id=cliente.id)\
                   .order_by(Interaccion.timestamp.desc()).all()

    def obtener_lotes_cliente(self, symbol: str) -> List[LoteCompra]:
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            return []
        return self.db.query(LoteCompra).filter_by(cliente_id=cliente.id)\
                   .order_by(LoteCompra.fecha_compra.asc()).all()

    def obtener_todos_lotes_con_clientes(self) -> Dict[str, List[LoteCompra]]:
        lotes = self.db.query(LoteCompra).join(ClienteCripto).filter(LoteCompra.cantidad_restante > 0).all()
        resultado = {}
        for lote in lotes:
            symbol = lote.cliente.symbol
            if symbol not in resultado:
                resultado[symbol] = []
            resultado[symbol].append(lote)
        return resultado

    def calcular_pnl_fifo_para_cliente(self, symbol: str, precio_actual: float) -> Dict[str, Any]:
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            return {"error": "Cliente no encontrado"}
        lotes = self.db.query(LoteCompra).filter(
            LoteCompra.cliente_id == cliente.id,
            LoteCompra.cantidad_restante > 0
        ).order_by(LoteCompra.fecha_compra.asc()).all()
        
        cantidad_total = 0.0
        costo_total = 0.0
        for lote in lotes:
            cant = float(lote.cantidad_restante)
            cantidad_total += cant
            costo_total += cant * float(lote.precio_unitario)
        
        valor_actual = cantidad_total * precio_actual
        pnl = valor_actual - costo_total
        return {
            "pnl_total": pnl,
            "costo_total": costo_total,
            "valor_actual": valor_actual,
            "cantidad_total": cantidad_total
        }

    # ═══════════════════════════════════════
    # OPORTUNIDADES
    # ═══════════════════════════════════════

    def crear_oportunidad(self, symbol: str, tipo: str,
                          entrada: float, objetivo: float, stop: float,
                          monto_planificado: float = 0,
                          confianza: int = 3, notas: str = "") -> Oportunidad:
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            raise ValueError(f"Cliente {symbol} no existe")

        riesgo = abs(entrada - stop)
        beneficio = abs(objetivo - entrada)
        rb = beneficio / riesgo if riesgo > 0 else 0

        tipo_enum = None
        for enum_member in TipoOportunidad:
            if enum_member.value == tipo:
                tipo_enum = enum_member
                break
        if not tipo_enum:
            raise ValueError(f"Tipo de oportunidad inválido: {tipo}. Debe ser uno de: {[e.value for e in TipoOportunidad]}")

        opp = Oportunidad(
            cliente_id=cliente.id,
            tipo=tipo_enum,
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

    def oportunidades_por_cliente(self, symbol: str) -> List[Oportunidad]:
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            return []
        return self.db.query(Oportunidad).filter_by(cliente_id=cliente.id)\
                   .order_by(Oportunidad.fecha_creacion.desc()).all()

    def oportunidades_por_estado_cliente(self, symbol: str, estado: str) -> List[Oportunidad]:
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            return []
        return self.db.query(Oportunidad).filter(
            Oportunidad.cliente_id == cliente.id,
            Oportunidad.estado == estado
        ).order_by(Oportunidad.fecha_creacion.desc()).all()

    def obtener_todas_oportunidades(self) -> List[Oportunidad]:
        return self.db.query(Oportunidad).order_by(Oportunidad.fecha_creacion.desc()).all()

    # ═══════════════════════════════════════
    # TAREAS
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
        """Devuelve todas las tareas no completadas, ordenadas por fecha límite (las más próximas primero)."""
        query = self.db.query(Tarea).filter(Tarea.completada == False)
        if urgentes:
            query = query.filter(Tarea.prioridad == 1)
        return query.order_by(Tarea.fecha_limite.asc()).all()

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