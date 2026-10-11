# Credenciales

En esta carpeta se encuentran la lista de secretos necesarios para GitHub
Actions y el script interactivo para sincronizarlos con este repositorio.

La lista completa, con el nombre, la descripción y el tipo de cada secreto, está en
`github_actions_secrets.json`. El script ofrece borrar los secretos de Actions
del repositorio que no figuren en la lista, incluidos los nombres que retires.
La confirmación general tiene «no» por defecto (Enter cancela el borrado).
Si aceptas, pregunta por cada secreto con «sí» por defecto (Enter lo elimina);
puedes responder «n» para conservarlo. Los secretos de organización, entornos, Dependabot y
Codespaces quedan fuera de esta sincronización.

Con GitHub CLI y `jq` instalados y una sesión con permisos para administrar secretos:

```bash
gh auth login
bash ops/credentials/configure_github_secrets.sh
```

Los valores se introducen sin mostrarlos en pantalla. Enter conserva un secreto
existente; si todavía no existe, es obligatorio introducirlo. El tipo `standard` pide un valor; el tipo `ssh_key` pide la ruta al archivo de
clave privada SSH.
