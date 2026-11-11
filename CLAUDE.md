# httpchat — notas del proyecto

Chat para red local por HTTP, en Python **solo con la biblioteca estándar** (Python ≥ 3.8, sin dependencias). No agregar dependencias externas.

- Repositorio público: https://github.com/rippsec/httpchat — licencia MIT, © 2026 rippsec.
- Código: `httpchat/server.py` (servidor y `main`), `httpchat/page.py` (HTML/JS de la página), `chat/` (alias para `python3 -m chat`).

## Uso

```bash
python3 -m chat 8082        # o: httpchat 8082
pipx install git+https://github.com/rippsec/httpchat.git   # instalar en otra máquina
```

Los demás en la misma red abren `http://<IP-de-la-máquina>:8082` en el navegador.

## Funciones actuales

- **Escritura en vivo:** todos ven lo que cada quien escribe y corrige, letra por letra, en un globo punteado ("✎ X está escribiendo…"). Quien escribe ve también su propio borrador (en azul). Al presionar Enter se envía y ya no se puede editar.
- Barra de conectados (hosts con la página abierta y quién está escribiendo).
- La IP como nombre por defecto si no se pone un nombre.
- Modo oscuro automático y diseño adaptable a móvil.
- Mensajes (últimos 500) en memoria; sin autenticación ni cifrado (solo redes de confianza).
