import javalang
from typing import Dict, Any, List
from logger import logger


def safe_to_dict(obj: Any) -> Any:
    """
    Recursively convert javalang nodes into JSON-serializable dicts.
    
    Args:
        obj: Object to convert
    
    Returns:
        JSON-serializable representation
    """
    if isinstance(obj, list):
        return [safe_to_dict(x) for x in obj]
    elif hasattr(obj, "__dict__"):
        result = {}
        for k, v in obj.__dict__.items():
            if k in ("position", "documentation", "annotations"):
                continue
            result[k] = safe_to_dict(v)
        return result
    elif isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    else:
        return str(obj)


def calculate_method_complexity(method_node) -> int:
    """
    Calculate cyclomatic complexity of a method.
    
    Args:
        method_node: javalang method node
    
    Returns:
        Cyclomatic complexity score
    """
    complexity = 1  # Base complexity
    
    if not method_node.body:
        return complexity
    
    body_str = str(safe_to_dict(method_node.body))
    
    # Count decision points
    decision_keywords = ['if', 'for', 'while', 'case', 'catch', '&&', '||', '?']
    for keyword in decision_keywords:
        complexity += body_str.lower().count(keyword)
    
    return complexity


def extract_method_info(method_node) -> Dict[str, Any]:
    """
    Extract detailed information from a method node.
    
    Args:
        method_node: javalang method declaration node
    
    Returns:
        Dictionary with method information
    """
    params = []
    if hasattr(method_node, 'parameters') and method_node.parameters:
        for param in method_node.parameters:
            param_type = param.type.name if hasattr(param.type, 'name') else str(param.type)
            params.append({
                "name": param.name,
                "type": param_type
            })
    
    return_type = "void"
    if hasattr(method_node, 'return_type') and method_node.return_type:
        return_type = method_node.return_type.name if hasattr(method_node.return_type, 'name') else str(method_node.return_type)
    
    # Convert set to list for JSON serialization
    modifiers = list(method_node.modifiers) if hasattr(method_node, 'modifiers') else []
    
    signature = f"{' '.join(modifiers)} {return_type} {method_node.name}({', '.join([f'{p['type']} {p['name']}' for p in params])})"
    
    complexity = calculate_method_complexity(method_node)
    
    return {
        "name": method_node.name,
        "signature": signature.strip(),
        "modifiers": modifiers,
        "return_type": return_type,
        "parameters": params,
        "complexity": complexity,
        "body": safe_to_dict(method_node.body) if method_node.body else None
    }


def parse_java_file(file_path: str) -> Dict[str, Any]:
    """
    Parse Java file for comprehensive class information.
    
    Args:
        file_path: Path to Java source file
    
    Returns:
        Dictionary containing parsed structure
    """
    with open(file_path, "r", encoding='utf-8') as f:
        code = f.read()
    
    result = {
        "file_path": file_path,
        "classes": [],
        "interfaces": [],
        "package": None,
        "imports": []
    }

    try:
        tree = javalang.parse.parse(code)
    except javalang.parser.JavaSyntaxError as e:
        logger.warning(f"Parse error in {file_path}: {e}")
        return result
    
    # Extract package
    if tree.package:
        result["package"] = tree.package.name
    
    # Extract imports
    if tree.imports:
        result["imports"] = [imp.path for imp in tree.imports]
    
    # Extract classes
    for _, class_node in tree.filter(javalang.tree.ClassDeclaration):
        methods = []
        fields = []
        
        # Extract methods
        for _, method_node in class_node.filter(javalang.tree.MethodDeclaration):
            methods.append(extract_method_info(method_node))
        
        # Extract fields
        for _, field_node in class_node.filter(javalang.tree.FieldDeclaration):
            field_type = field_node.type.name if hasattr(field_node.type, 'name') else str(field_node.type)
            for declarator in field_node.declarators:
                fields.append({
                    "name": declarator.name,
                    "type": field_type,
                    "modifiers": list(field_node.modifiers) if hasattr(field_node, 'modifiers') else []
                })
        
        class_info = {
            "name": class_node.name,
            "type": "class",
            "modifiers": list(class_node.modifiers) if hasattr(class_node, 'modifiers') else [],
            "extends": class_node.extends.name if getattr(class_node, "extends", None) else None,
            "implements": [impl.name for impl in getattr(class_node, "implements", []) or []],
            "methods": methods,
            "fields": fields,
            "method_count": len(methods),
            "field_count": len(fields),
            "avg_complexity": sum(m["complexity"] for m in methods) / len(methods) if methods else 0
        }
        result["classes"].append(class_info)
    
    # Extract interfaces
    for _, interface_node in tree.filter(javalang.tree.InterfaceDeclaration):
        methods = []
        for _, method_node in interface_node.filter(javalang.tree.MethodDeclaration):
            methods.append(extract_method_info(method_node))
        
        interface_info = {
            "name": interface_node.name,
            "type": "interface",
            "extends": [ext.name for ext in getattr(interface_node, "extends", []) or []],
            "methods": methods,
            "method_count": len(methods)
        }
        result["interfaces"].append(interface_info)
    
    return result