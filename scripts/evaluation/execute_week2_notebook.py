"""Execute the Week 2 notebook using the invoking environment and saved artifacts."""

import json
from pathlib import Path
import sys
import tempfile

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager

ROOT = Path(__file__).resolve().parents[2]


def execute_notebook(notebook, root=ROOT, timeout=180):
    """Bind the kernel to this interpreter without changing Jupyter settings."""
    with tempfile.TemporaryDirectory(prefix="ingen-notebook-") as temporary:
        directory = Path(temporary)/"ingen-evaluation"
        directory.mkdir()
        (directory/"kernel.json").write_text(json.dumps({
            "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
            "env": {"MPLBACKEND": "module://matplotlib_inline.backend_inline"},
            "display_name": "Evaluation Python", "language": "python"}))
        specs = KernelSpecManager(kernel_dirs=[temporary])
        manager = KernelManager(kernel_name="ingen-evaluation", kernel_spec_manager=specs)
        client = NotebookClient(notebook, km=manager, timeout=timeout,
                                resources={"metadata": {"path": str(root)}})
        try:
            client.execute()
        finally:
            if manager.has_kernel:
                manager.shutdown_kernel(now=True)
    assert all(output.get("output_type") != "error" for cell in notebook.cells
               if cell.cell_type == "code" for output in cell.get("outputs", []))
    return notebook


def execute():
    """Execute saved RAG cells using the invoking environment."""
    path = ROOT/"notebooks/rag_evaluation.ipynb"
    notebook = nbformat.read(path, as_version=4)
    execute_notebook(notebook)
    nbformat.write(notebook, path)
    print("All Week 2 notebook code cells executed; saved-score replay is exact.")


if __name__ == "__main__":
    execute()
