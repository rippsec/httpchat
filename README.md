# httpchat

Chat para red local por HTTP, sin dependencias (solo la biblioteca estándar de Python ≥ 3.8).
Los demás solo necesitan abrir una URL en el navegador.

## Funciones

- **Escritura en vivo:** se ve lo que cada persona va escribiendo (y corrigiendo) letra por letra; al presionar **Enter** se envía y ya no se puede editar.
- **Barra de conectados:** lista de hosts con la página abierta y quién está escribiendo.
- **La IP como nombre por defecto** si no se pone un nombre.
- Modo oscuro automático y diseño adaptable a móvil.

## Uso

```bash
git clone https://github.com/rippsec/httpchat.git
cd httpchat
python3 -m chat 8082        # o: python3 -m httpchat -p 8082
```

Al arrancar muestra la URL de la red local (ej. `http://192.168.1.10:8082`); compártela con quien esté en la misma red.

### Instalarlo como comando

```bash
pipx install git+https://github.com/rippsec/httpchat.git
httpchat 8082
```

Opciones: `httpchat [PUERTO] [-H HOST]` (por defecto `0.0.0.0:8000`).

Si otras máquinas no conectan, abre el puerto en el firewall (ej. `sudo ufw allow 8082/tcp`).

## Notas

- Sin autenticación ni cifrado: cualquiera en la red puede entrar. Úsalo solo en redes de confianza.
- Los mensajes (últimos 500) viven en memoria y se pierden al detener el servidor.
- La lista de conectados cuenta pestañas, no máquinas.

## Uso desde Python

```python
from httpchat import serve
serve(host="0.0.0.0", port=8082)
```
