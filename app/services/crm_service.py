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
            query = query.filter(ClienteCripto.roi_porcentaje >= Decimal(str(min_roi)))
        if tags:
            query = query.filter(ClienteCripto.tags.contains(tags))
        return query.order_by(ClienteCripto.prioridad).all()

    def actualizar_estado_cliente(self, symbol: str) -> Optional[ClienteCripto]:
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            return None

        roi = cliente.roi_porcentaje if cliente.roi_porcentaje else Decimal("0")
        cantidad = cliente.cantidad_total if cliente.cantidad_total else Decimal("0")

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
        print(f"[ACTUALIZAR PRECIO] {symbol} -> {precio}")
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            raise ValueError(f"Cliente {symbol} no encontrado")

        if precio is None or str(precio).strip().lower() in ["none", "null", ""]:
            print(f"[WARN] Precio no disponible o invalido para {symbol}. Se omite actualizacion de mercado.")
            return cliente

        try:
            precio_dec = Decimal(str(precio))
        except Exception:
            print(f"[ERROR] No se pudo parsear el precio {precio} para {symbol}.")
            return cliente

        cliente.precio_actual = precio_dec
        cantidad = cliente.cantidad_total if cliente.cantidad_total else Decimal("0")

        if cantidad > 0:
            cliente.valor_mercado = precio_dec * cantidad
            costo_promedio = cliente.costo_promedio if cliente.costo_promedio else Decimal("0")
            costo_total = cantidad * costo_promedio
            if costo_total > 0:
                cliente.pnl_total = cliente.valor_mercado - costo_total
                cliente.roi_porcentaje = (cliente.pnl_total / costo_total) * Decimal("100")

        self.db.commit()
        self.actualizar_estado_cliente(symbol)
        return cliente

    def corregir_inversion_total(self, symbol: str, nueva_inversion: float) -> ClienteCripto:
        """Permite sobreescribir manualmente el capital invertido en caso de desfase."""
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            raise ValueError(f"Cliente {symbol} no encontrado")
        
        cliente.inversion_total = Decimal(str(nueva_inversion))
        
        precio_actual = cliente.precio_actual if cliente.precio_actual else Decimal("0")
        cantidad = cliente.cantidad_total if cliente.cantidad_total else Decimal("0")
        cliente.valor_mercado = precio_actual * cantidad
        
        if cliente.inversion_total > 0:
            cliente.pnl_total = cliente.valor_mercado - cliente.inversion_total
            cliente.roi_porcentaje = (cliente.pnl_total / cliente.inversion_total) * Decimal("100")
        else:
            cliente.pnl_total = cliente.valor_mercado
            cliente.roi_porcentaje = Decimal("0")
            
        self.db.commit()
        self.db.refresh(cliente)
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

        cant_dec = Decimal(str(cantidad))
        prec_dec = Decimal(str(precio))
        fee_dec = Decimal(str(fee))

        costo_total = (cant_dec * prec_dec) + fee_dec
        precio_con_fee = costo_total / cant_dec

        lote = LoteCompra(
            cliente_id=cliente.id,
            cantidad=cant_dec,
            cantidad_restante=cant_dec,
            precio_unitario=precio_con_fee,
            exchange=exchange,
            notas=notas
        )
        self.db.add(lote)

        monto = cant_dec * prec_dec
        interaccion = Interaccion(
            cliente_id=cliente.id,
            tipo=TipoInteraccion.COMPRA,
            cantidad=cant_dec,
            precio_unitario=prec_dec,
            monto_usd=monto,
            fee=fee_dec,
            exchange=exchange,
            notas=notas
        )
        self.db.add(interaccion)

        cant_previa = cliente.cantidad_total if cliente.cantidad_total else Decimal("0")
        costo_prom_previo = cliente.costo_promedio if cliente.costo_promedio else Decimal("0")
        
        total_previo = cant_previa * costo_prom_previo
        total_nuevo = costo_total
        nueva_cantidad = cant_previa + cant_dec
        
        if nueva_cantidad > 0:
            cliente.costo_promedio = (total_previo + total_nuevo) / nueva_cantidad
        
        cliente.cantidad_total = nueva_cantidad
        cliente.inversion_total = (cliente.inversion_total if cliente.inversion_total else Decimal("0")) + costo_total

        self.db.commit()
        self.db.refresh(lote)
        self.actualizar_estado_cliente(symbol)

        return {"lote": lote, "interaccion": interaccion}

    def registrar_venta_fifo(self, symbol: str, cantidad_vender: float, precio_venta: float,
                             fee: float = 0.0, exchange: str = "binance", notas: str = "") -> Dict[str, Any]:
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            raise ValueError(f"Cliente {symbol} no existe")

        cant_vender_dec = Decimal(str(cantidad_vender))
        prec_venta_dec = Decimal(str(precio_venta))
        fee_dec = Decimal(str(fee))

        cant_total_cliente = cliente.cantidad_total if cliente.cantidad_total else Decimal("0")
        if cant_vender_dec > cant_total_cliente:
            raise ValueError(f"No hay suficiente cantidad para vender. Disponible: {cant_total_cliente}")

        lotes = self.db.query(LoteCompra).filter(
            LoteCompra.cliente_id == cliente.id,
            LoteCompra.cantidad_restante > 0
        ).order_by(LoteCompra.fecha_compra.asc()).all()

        if not lotes:
            raise ValueError("No hay lotes de compra para este cliente")

        cantidad_a_vender = cant_vender_dec
        pnl_total = Decimal("0")
        detalles_consumo = []

        for lote in lotes:
            if cantidad_a_vender <= 0:
                break
            disponible = lote.cantidad_restante
            a_consumir = min(disponible, cantidad_a_vender)

            precio_compra_con_fee = lote.precio_unitario
            pnl_lote = (prec_venta_dec - precio_compra_con_fee) * a_consumir
            pnl_total += pnl_lote

            lote.cantidad_restante -= a_consumir
            cantidad_a_vender -= a_consumir

            detalles_consumo.append({
                "lote_id": lote.id,
                "cantidad": float(a_consumir),
                "precio_compra": float(precio_compra_con_fee),
                "pnl_lote": float(pnl_lote)
            })

        pnl_total -= fee_dec
        cantidad_vendida = cant_vender_dec - cantidad_a_vender
        monto = cantidad_vendida * prec_venta_dec

        interaccion = Interaccion(
            cliente_id=cliente.id,
            tipo=TipoInteraccion.VENTA,
            cantidad=cantidad_vendida,
            precio_unitario=prec_venta_dec,
            monto_usd=monto,
            fee=fee_dec,
            exchange=exchange,
            notas=notas,
            pnl_realizado=pnl_total
        )
        self.db.add(interaccion)

        nueva_cantidad = cant_total_cliente - cantidad_vendida
        cliente.cantidad_total = nueva_cantidad
        cliente.pnl_total = (cliente.pnl_total if cliente.pnl_total else Decimal("0")) + pnl_total

        # CORRECCIÓN CONTABLE: Al vender, se descarga el capital base de los lotes restantes
        if nueva_cantidad > 0:
            lotes_restantes = self.db.query(LoteCompra).filter(
                LoteCompra.cliente_id == cliente.id,
                LoteCompra.cantidad_restante > 0
            ).all()
            inversion_restante = sum(l.cantidad_restante * l.precio_unitario for l in lotes_restantes)
            cliente.costo_promedio = inversion_restante / nueva_cantidad
            cliente.inversion_total = inversion_restante
        else:
            cliente.costo_promedio = Decimal("0")
            cliente.inversion_total = Decimal("0")

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
        
        cant_dec = Decimal(str(cantidad))
        prec_dec = Decimal(str(precio))
        fee_dec = Decimal(str(fee))
        
        interaccion = Interaccion(
            cliente_id=cliente.id,
            tipo=TipoInteraccion(tipo),
            cantidad=cant_dec,
            precio_unitario=prec_dec,
            monto_usd=cant_dec * prec_dec,
            fee=fee_dec,
            exchange=exchange,
            notas=notas
        )
        self.db.add(interaccion)
        if tipo in ["staking", "airdrop", "dividendo"]:
            cliente.cantidad_total = (cliente.cantidad_total if cliente.cantidad_total else Decimal("0")) + cant_dec
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
            cantidad = inter.cantidad
            precio = inter.precio_unitario
            fee = inter.fee

            if tipo == "compra":
                costo_total = (cantidad * precio) + fee
                precio_con_fee = costo_total / cantidad

                lote = LoteCompra(
                    cliente_id=cliente.id,
                    cantidad=cantidad,
                    cantidad_restante=cantidad,
                    precio_unitario=precio_con_fee,
                    exchange=inter.exchange,
                    notas=inter.notas
                )
                self.db.add(lote)

                total_previo = cliente.cantidad_total * cliente.costo_promedio
                nueva_cantidad = cliente.cantidad_total + cantidad
                if nueva_cantidad > 0:
                    cliente.costo_promedio = (total_previo + costo_total) / nueva_cantidad
                cliente.cantidad_total = nueva_cantidad
                cliente.inversion_total += costo_total

            elif tipo == "venta":
                lotes = self.db.query(LoteCompra).filter(
                    LoteCompra.cliente_id == cliente.id,
                    LoteCompra.cantidad_restante > 0
                ).order_by(LoteCompra.fecha_compra.asc()).all()

                cantidad_a_vender = cantidad
                pnl_total = Decimal("0")

                for lote in lotes:
                    if cantidad_a_vender <= 0:
                        break
                    disponible = lote.cantidad_restante
                    a_consumir = min(disponible, cantidad_a_vender)

                    pnl_lote = (precio - lote.precio_unitario) * a_consumir
                    pnl_total += pnl_lote

                    lote.cantidad_restante -= a_consumir
                    cantidad_a_vender -= a_consumir

                pnl_total -= fee
                cantidad_vendida = cantidad - cantidad_a_vender

                nueva_cantidad = cliente.cantidad_total - cantidad_vendida
                cliente.cantidad_total = nueva_cantidad
                cliente.pnl_total += pnl_total

                # CORRECCIÓN CONTABLE
                if nueva_cantidad > 0:
                    lotes_restantes = self.db.query(LoteCompra).filter(
                        LoteCompra.cliente_id == cliente.id,
                        LoteCompra.cantidad_restante > 0
                    ).all()
                    inversion_restante = sum(l.cantidad_restante * l.precio_unitario for l in lotes_restantes)
                    cliente.costo_promedio = inversion_restante / nueva_cantidad
                    cliente.inversion_total = inversion_restante
                else:
                    cliente.costo_promedio = Decimal("0")
                    cliente.inversion_total = Decimal("0")

                inter.pnl_realizado = pnl_total

            else:
                if tipo in ["staking", "airdrop", "dividendo"]:
                    cliente.cantidad_total += cantidad

        if cliente.cantidad_total > 0:
            precio_actual = cliente.precio_actual if cliente.precio_actual else Decimal("0")
            cliente.valor_mercado = precio_actual * cliente.cantidad_total
            inversion_total = cliente.inversion_total
            if inversion_total > 0:
                cliente.pnl_total = cliente.valor_mercado - inversion_total
                cliente.roi_porcentaje = (cliente.pnl_total / inversion_total) * Decimal("100")

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
        
        cantidad_total = Decimal("0")
        costo_total = Decimal("0")
        for lote in lotes:
            cant = lote.cantidad_restante
            cantidad_total += cant
            costo_total += cant * lote.precio_unitario
        
        precio_dec = Decimal(str(precio_actual))
        valor_actual = cantidad_total * precio_dec
        pnl = valor_actual - costo_total
        return {
            "pnl_total": float(pnl),
            "costo_total": float(costo_total),
            "valor_actual": float(valor_actual),
            "cantidad_total": float(cantidad_total)
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
            if enum_member.value == tipo or enum_member.name == tipo.upper():
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
        query = self.db.query(Tarea).filter(Tarea.completada == False)
        if urgentes:
            query = query.filter(Tarea.prioridad == 1)
        return query.order_by(Tarea.fecha_limite.asc()).all()

    def tareas_proximas(self, dias: int = 3) -> List[Tarea]:
        limite = datetime.utcnow() + timedelta(days=dias)
        return self.db.query(Tarea).filter(
            Tarea.completada == False,
            Tarea.fecha_limite <= limite,
            Tarea.fecha_limite > datetime.utcnow()
        ).order_by(Tarea.fecha_limite).all()

    def tareas_completadas(self, limit: int = 10) -> List[Tarea]:
        return self.db.query(Tarea).filter(Tarea.completada == True)\
            .order_by(Tarea.fecha_completada.desc()).limit(limit).all()

    # ═══════════════════════════════════════
    # ANALYTICS & REPORTES
    # ═══════════════════════════════════════

    def resumen_portafolio(self) -> dict:
        clientes = self.db.query(ClienteCripto).all()
        interacciones = self.db.query(Interaccion).count()
        oportunidades_abiertas = self.db.query(Oportunidad).filter_by(estado="abierta").count()
        tareas_pend = len(self.tareas_pendientes())

        total_invertido = sum(c.inversion_total for c in clientes) if clientes else Decimal("0")
        total_valor = sum(c.valor_mercado for c in clientes) if clientes else Decimal("0")
        pnl_total = total_valor - total_invertido
        roi = (pnl_total / total_invertido * Decimal("100")) if total_invertido > 0 else Decimal("0")

        return {
            "total_clientes": len(clientes),
            "clientes_activos": len([c for c in clientes if c.cantidad_total > 0]),
            "clientes_vip": len([c for c in clientes if c.estado == EstadoCliente.VIP]),
            "clientes_peligro": len([c for c in clientes if c.estado == EstadoCliente.ACTIVO_PELIGRO]),
            "total_invertido": round(float(total_invertido), 2),
            "total_valor_mercado": round(float(total_valor), 2),
            "pnl_total": round(float(pnl_total), 2),
            "roi_porcentaje": round(float(roi), 2),
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