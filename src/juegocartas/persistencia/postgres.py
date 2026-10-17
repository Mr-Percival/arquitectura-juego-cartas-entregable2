"""PostgresRepositoryAdapter: implementa IRepositorioPartidas con una transacción por cierre (sección 2.4)."""
from __future__ import annotations

from psycopg.rows import dict_row

from juegocartas.nucleo.soporte.historial import CierreRonda, RondaYaLiquidada

BLOQUEAR_RONDA = "SELECT estado FROM ronda WHERE ronda_id = %s FOR UPDATE"
REGISTRAR_JUGADA = ("INSERT INTO turno_jugada (mano_id, numero_turno, accion, resultado, comando_id) "
                    "SELECT mano_id, %s, 'SOLICITAR_CIERRE', 'ACEPTADA', %s FROM mano_jugador "
                    "WHERE ronda_id = %s AND jugador_id = %s")
CERRAR_RONDA = ("UPDATE ronda SET estado = 'LIQUIDADA', cerrada_por = %s, tipo_cierre = %s, "
                "cerrada_en = now() WHERE ronda_id = %s")
INSERTAR_PUNTAJE_RONDA = ("INSERT INTO puntaje_ronda (ronda_id, jugador_id, penalizacion, bonificacion) "
                          "VALUES (%s, %s, %s, %s)")
ACUMULAR = ("UPDATE puntaje_acumulado SET total = total + %s, version = version + 1, actualizado_en = now() "
            "WHERE partida_id = %s AND jugador_id = %s")
ELIMINAR = ("UPDATE participacion SET estado_jugador = 'ELIMINADO' "
            "WHERE partida_id = %s AND jugador_id = %s")
FINALIZAR = ("UPDATE partida SET estado = 'FINALIZADA', ganador_id = %s, finalizada_en = now() "
             "WHERE partida_id = %s")


class PostgresRepositoryAdapter:
    def __init__(self, conexion) -> None:  # conexión psycopg 3
        self._cx = conexion

    def liquidar_ronda(self, c: CierreRonda) -> None:
        """Todo o nada: si algo falla (o la ronda ya fue liquidada) no queda ninguna escritura parcial."""
        with self._cx.transaction(), self._cx.cursor() as cur:
            cur.execute(BLOQUEAR_RONDA, (c.ronda_id,))
            if cur.fetchone()[0] != "EN_JUEGO":
                raise RondaYaLiquidada(c.ronda_id)
            cur.execute(REGISTRAR_JUGADA, (c.numero_turno, c.comando_id, c.ronda_id, c.jugador_cierra))
            cur.execute(CERRAR_RONDA, (c.jugador_cierra, c.tipo_cierre, c.ronda_id))
            for jugador, penalizacion in c.penalizaciones.items():
                bono = c.bonificaciones.get(jugador, 0)
                cur.execute(INSERTAR_PUNTAJE_RONDA, (c.ronda_id, jugador, penalizacion, bono))
                cur.execute(ACUMULAR, (penalizacion - bono, c.partida_id, jugador))
            for jugador in c.eliminados:
                cur.execute(ELIMINAR, (c.partida_id, jugador))
            if c.partida_terminada:
                cur.execute(FINALIZAR, (c.ganador, c.partida_id))

    def historial(self, partida_id: str) -> list[dict]:
        with self._cx.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM v_historial_puntajes WHERE partida_id = %s ORDER BY numero", (partida_id,))
            return cur.fetchall()
