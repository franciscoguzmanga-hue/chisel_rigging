import os
import ast

def extract_python_content(filepath):
    """Extrae clases, funciones y métodos de un archivo Python"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        content = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                content.append(('class', node.name, node.lineno))
                # Extraer métodos de la clase
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        content.append(('method', item.name, item.lineno))
            elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                # Solo funciones de nivel superior (no métodos)
                content.append(('function', node.name, node.lineno))
        
        # Ordenar por línea
        content.sort(key=lambda x: x[2])
        return content
    except Exception as e:
        return None

def print_tree(directory, prefix="", is_last=True, show_content=True):
    """Imprime el árbol de archivos de un directorio con contenido de archivos .py"""
    try:
        items = sorted(os.listdir(directory))
    except PermissionError:
        print(f"{prefix}[Acceso denegado]")
        return
    
    # Separar directorios y archivos
    dirs = [item for item in items if os.path.isdir(os.path.join(directory, item))]
    files = [item for item in items if os.path.isfile(os.path.join(directory, item))]
    
    # Combinar directorios primero, luego archivos
    all_items = dirs + files
    
    for i, item in enumerate(all_items):
        is_last_item = (i == len(all_items) - 1)
        connector = "└── " if is_last_item else "├── "
        
        item_path = os.path.join(directory, item)
        
        # Imprimir directorio o archivo
        if os.path.isdir(item_path):
            print(f"{prefix}{connector}📁 {item}")
            extension = "    " if is_last_item else "│   "
            print_tree(item_path, prefix + extension, is_last_item, show_content)
        else:
            # Mostrar icono según tipo de archivo
            icon = "🐍" if item.endswith('.py') else "📄"
            print(f"{prefix}{connector}{icon} {item}")
            
            # Si es archivo Python, mostrar contenido
            if show_content and item.endswith('.py'):
                content = extract_python_content(item_path)
                if content:
                    extension = "    " if is_last_item else "│   "
                    for j, (item_type, name, line) in enumerate(content):
                        is_last_content = (j == len(content) - 1)
                        content_connector = "└── " if is_last_content else "├── "
                        
                        if item_type == 'class':
                            print(f"{prefix}{extension}{content_connector}🔷 class {name} (línea {line})")
                        elif item_type == 'function':
                            print(f"{prefix}{extension}{content_connector}🔹 def {name}() (línea {line})")
                        elif item_type == 'method':
                            print(f"{prefix}{extension}│   └── 🔸 def {name}() (línea {line})")

# Ruta al directorio 5_app
base_dir = os.path.join(os.path.dirname(__file__), "..")
print(f"\n{'='*80}")
print(f"Árbol de archivos de: {os.path.abspath(base_dir)}")
print(f"{'='*80}\n")
print(f"📁 {os.path.basename(base_dir)}")
print_tree(base_dir, show_content=True)
print(f"\n{'='*80}")


