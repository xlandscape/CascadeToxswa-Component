"""
Script for documenting the code of the CascadeToxswa component.
"""
import os
import base.documentation
import CascadeToxswa

root_folder = os.path.abspath(os.path.join(os.path.dirname(base.__file__), ".."))
base.documentation.document_component(
    CascadeToxswa.CascadeToxswa("CascadeToxswa", None, None),
    os.path.join(root_folder, "..", "variant", "CascadeToxswa", "README.md"),
    os.path.join(root_folder, "..", "variant", "mc.xml")
)
base.documentation.write_changelog(
    "CascadeToxswa component",
    CascadeToxswa.CascadeToxswa.VERSION,
    os.path.join(root_folder, "..", "variant", "CascadeToxswa", "CHANGELOG.md")
)
base.documentation.write_contribution_notes(
    os.path.join(root_folder, "..", "variant", "CascadeToxswa", "CONTRIBUTING.md"))
