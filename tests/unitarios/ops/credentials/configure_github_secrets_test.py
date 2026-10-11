"""Pruebas de ops/credentials/configure_github_secrets.sh con gh simulado.

Cubren creación, conservación, actualización, claves multilínea y retirada de
secretos, selección de entrada según el tipo y confirmaciones de borrado.
También cubren el bloqueo del borrado ante lista inválida, fallo de gh o EOF.
No acceden a GitHub ni verifican autenticación real, cifrado o permisos remotos.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[4]
NAMES = ["DOCKER_HUB_USERNAME", "DOCKER_HUB_TOKEN", "REMOTE_HOST", "REMOTE_USER", "REMOTE_SSH_KEY"]
FAKE_GH = r'''#!/usr/bin/python3
import json
import os
from pathlib import Path
import sys

path = Path(os.environ["TEST_GH_STATE"])
state = json.loads(path.read_text())
args = sys.argv[1:]
state["calls"].append(args)
path.write_text(json.dumps(state))
if args[:2] == ["auth", "status"]:
    sys.exit(0)
assert "--repo" in args and args[args.index("--repo") + 1] == "Serhuela/proj-fund_nav_fetcher-python"
assert "--app" in args and args[args.index("--app") + 1] == "actions"
if args[:2] == ["secret", "list"]:
    if state.get("fail") == "list":
        sys.exit(1)
    print("\n".join(sorted(state["secrets"])))
elif args[:2] == ["secret", "set"]:
    if state.get("fail") == "set":
        sys.exit(1)
    state["secrets"][args[2]] = sys.stdin.read()
    path.write_text(json.dumps(state))
elif args[:2] == ["secret", "delete"]:
    del state["secrets"][args[2]]
    path.write_text(json.dumps(state))
else:
    sys.exit(2)
'''


class ConfigureGithubSecretsTest(unittest.TestCase):
    """Ejecuta el script con entradas controladas sin invocar la CLI real."""

    def setUp(self) -> None:
        """Prepara una copia aislada del script, su lista y la CLI simulada."""
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        source = PROJECT_ROOT / "ops" / "credentials"
        self.script = self.folder / "configure_github_secrets.sh"
        shutil.copyfile(source / self.script.name, self.script)
        self.list_file = self.folder / "github_actions_secrets.json"
        shutil.copyfile(source / self.list_file.name, self.list_file)
        self.state_file = self.folder / "state.json"
        gh = self.folder / "gh"
        gh.write_text(FAKE_GH)
        gh.chmod(0o755)
        self.env = dict(os.environ, PATH=f"{self.folder}:{os.environ['PATH']}",
                        TEST_GH_STATE=str(self.state_file))
        self.original = {name: f"original-{name}" for name in NAMES}

    def run_script(self, values: str, secrets: dict, fail: str = "") -> tuple:
        """Ejecuta con valores de prueba y devuelve el resultado y el estado remoto."""
        self.state_file.write_text(json.dumps({"secrets": secrets, "calls": [], "fail": fail}))
        result = subprocess.run(["bash", str(self.script)], input=values, text=True,
                                capture_output=True, env=self.env, timeout=10)
        return result, json.loads(self.state_file.read_text())

    def test_enter_conserva_y_borra_solo_los_ausentes_de_la_lista(self) -> None:
        """Mantiene los cinco valores existentes y elimina el secreto retirado."""
        result, state = self.run_script("\n" * 5 + "s\n\n", self.original | {"RETIRED_SECRET": "anterior"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(state["secrets"], self.original)
        self.assertFalse(any(call[:2] == ["secret", "set"] for call in state["calls"]))
        self.assertEqual(result.stdout.count("dejar vacío para mantener el valor que hay"), 5)

    def test_crea_secretos_y_carga_clave_multilinea_sin_mostrar_valores(self) -> None:
        """Envía valores por stdin y conserva los saltos de línea de la clave."""
        key = self.folder / "clave privada.pem"
        key.write_text("-----BEGIN KEY-----\nclave-de-prueba\n-----END KEY-----\n")
        values = ["usuario", "token-'$()-de-prueba", "host", "ssh-user", str(key)]
        result, state = self.run_script("\n".join(values) + "\n", {})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(state["secrets"], dict(zip(NAMES, values[:4] + [key.read_text()])))
        self.assertNotIn(values[1], result.stdout + result.stderr)
        self.assertNotIn("clave-de-prueba", result.stdout + result.stderr)
        self.assertTrue(all("--body" not in call for call in state["calls"]))

    def test_secreto_nuevo_vacio_se_vuelve_a_pedir(self) -> None:
        """No crea un secreto vacío ni interpreta Enter como conservación si falta."""
        secrets = {name: value for name, value in self.original.items() if name != NAMES[0]}
        result, state = self.run_script("\nusuario-nuevo\n" + "\n" * 4, secrets)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(state["secrets"][NAMES[0]], "usuario-nuevo")
        self.assertIn("Este secreto no existe", result.stdout)

    def test_retirar_nombre_de_la_lista_elimina_el_secreto(self) -> None:
        """La lista modificada determina qué secretos se conservan."""
        entries = json.loads(self.list_file.read_text())
        self.list_file.write_text(json.dumps(entries[:-1]))
        result, state = self.run_script("\n" * 4 + "s\n\n", self.original)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("REMOTE_SSH_KEY", state["secrets"])

    def test_eof_impide_el_borrado(self) -> None:
        """Una entrada interrumpida no inicia la limpieza de secretos anteriores."""
        secrets = self.original | {"RETIRED_SECRET": "anterior"}
        result, state = self.run_script("\n", secrets)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(state["secrets"], secrets)
        self.assertFalse(any(call[:2] == ["secret", "delete"] for call in state["calls"]))

    def test_fallo_de_gh_impide_el_borrado(self) -> None:
        """Un fallo al consultar o guardar no elimina otros secretos."""
        for failure in ("list", "set"):
            with self.subTest(failure=failure):
                secrets = self.original | {"RETIRED_SECRET": "anterior"}
                result, state = self.run_script("nuevo\n" + "\n" * 4, secrets, failure)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(state["secrets"], secrets)
                self.assertFalse(any(call[:2] == ["secret", "delete"] for call in state["calls"]))

    def test_lista_vacia_invalida_o_duplicada_no_accede_a_github(self) -> None:
        """Evita que una lista dañada vacíe los secretos del repositorio."""
        invalid_entries = [
            [],
            [{"name": "nombre inválido", "description": "Descripción"}],
            [{"name": "REMOTE_HOST", "description": "Descripción"}] * 2,
            [{"name": "REMOTE_HOST"}],
            [{"name": "REMOTE_HOST", "description": "   "}],
            [{"name": "REMOTE_HOST", "description": 123}],
            {"name": "REMOTE_HOST", "description": "Descripción"},
        ]
        for entries in invalid_entries:
            if isinstance(entries, list):
                for entry in entries:
                    entry.setdefault("type", "standard")
        invalid_entries.extend([
            [{"name": "REMOTE_HOST", "description": "Descripción"}],
            [{"name": "REMOTE_HOST", "description": "Descripción", "type": "unknown"}],
            [{"name": "REMOTE_HOST", "description": "Descripción", "type": None}],
        ])
        for content in [json.dumps(entries) for entries in invalid_entries] + ["{JSON roto"]:
            with self.subTest(content=content):
                self.list_file.write_text(content)
                result, state = self.run_script("", self.original)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(state["calls"], [])

    def test_muestra_la_descripcion_de_cada_secreto(self) -> None:
        """Los prompts usan las descripciones de la configuración JSON."""
        entries = json.loads(self.list_file.read_text())
        entries[0]["description"] = "Descripción modificada para el usuario."
        self.list_file.write_text(json.dumps(entries))
        result, _ = self.run_script("\n" * 5, self.original)
        self.assertEqual(result.returncode, 0, result.stderr)
        for entry in entries:
            self.assertIn(entry["description"], result.stdout)

    def test_tipo_ssh_key_admite_un_nombre_distinto(self) -> None:
        """El tipo determina la carga de archivo aunque el secreto cambie de nombre."""
        key = self.folder / "otra clave.pem"
        key.write_text("-----BEGIN KEY-----\ncontenido-de-prueba\n-----END KEY-----\n")
        entries = json.loads(self.list_file.read_text())
        entries[-1]["name"] = "ANOTHER_SSH_KEY"
        self.list_file.write_text(json.dumps(entries))
        result, state = self.run_script("\n" * 4 + str(key) + "\ns\n\n", self.original)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(state["secrets"]["ANOTHER_SSH_KEY"], key.read_text())
        self.assertIn("Introduce la ruta al archivo", result.stdout)

    def test_tipo_standard_pide_valor_aunque_el_nombre_sea_remote_ssh_key(self) -> None:
        """Un secreto estándar se carga como texto sin tratarlo como ruta."""
        entries = json.loads(self.list_file.read_text())
        entries[-1]["type"] = "standard"
        self.list_file.write_text(json.dumps(entries))
        result, state = self.run_script("\n" * 4 + "valor-de-prueba\n", self.original)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(state["secrets"]["REMOTE_SSH_KEY"], "valor-de-prueba")
        self.assertIn("Introduce el valor de REMOTE_SSH_KEY", result.stdout)

    def test_confirmacion_general_enter_o_no_conserva_los_sobrantes(self) -> None:
        """La confirmación general no borra por defecto ni tras un no explícito."""
        secrets = self.original | {"RETIRED_SECRET": "anterior"}
        for answer in ("\n", "n\n"):
            with self.subTest(answer=answer):
                result, state = self.run_script("\n" * 5 + answer, secrets)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(state["secrets"], secrets)
                self.assertIn("¿Quieres proceder con el borrado? [s/N]", result.stdout)
                self.assertNotIn("¿Borrar el secreto", result.stdout)

    def test_confirmacion_individual_no_conserva_y_enter_borra(self) -> None:
        """Permite conservar un sobrante y borrar el siguiente mediante Enter."""
        secrets = self.original | {"OLD_A": "anterior-a", "OLD_B": "anterior-b"}
        result, state = self.run_script("\n" * 5 + "s\nn\n\n", secrets)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(state["secrets"], self.original | {"OLD_A": "anterior-a"})
        self.assertIn("¿Borrar el secreto OLD_A? [S/n]", result.stdout)
        self.assertIn("¿Borrar el secreto OLD_B? [S/n]", result.stdout)

    def test_confirmacion_invalida_se_repite_sin_borrar(self) -> None:
        """Una respuesta desconocida no autoriza el borrado y vuelve a preguntar."""
        secrets = self.original | {"RETIRED_SECRET": "anterior"}
        result, state = self.run_script("\n" * 5 + "quizá\nsí\nquizá\nno\n", secrets)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(state["secrets"], secrets)
        self.assertEqual(result.stdout.count("Responde s o n"), 2)

    def test_eof_en_confirmaciones_no_borra(self) -> None:
        """Un EOF general o individual no se interpreta como Enter para borrar."""
        secrets = self.original | {"RETIRED_SECRET": "anterior"}
        for answers in ("", "s\n"):
            with self.subTest(answers=answers):
                result, state = self.run_script("\n" * 5 + answers, secrets)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(state["secrets"], secrets)

    def test_sin_sobrantes_no_pide_confirmacion(self) -> None:
        """No pregunta por el borrado si todos los secretos figuran en el JSON."""
        result, state = self.run_script("\n" * 5, self.original)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(state["secrets"], self.original)
        self.assertNotIn("¿Quieres proceder con el borrado?", result.stdout)
