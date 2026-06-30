def _node_text(node, source):
    return source[node.start_byte:node.end_byte].decode('utf-8', errors='replace')

def _walk_tree(node, types):
    results = []
    if node.type in types:
        results.append(node)
    for child in node.children:
        results.extend(_walk_tree(child, types))
    return results

def extract_python_rich(source):
    from extraction.ts_parser import parse_code
    tree = parse_code(source, 'python')
    if not tree:
        return {}, []
    
    root = tree.root_node
    imports = []
    for n in _walk_tree(root, {'import_statement', 'import_from_statement'}):
        imports.append(_node_text(n, source).strip())
        
    def get_docstring(node):
        body = node.child_by_field_name('body')
        if body and body.children and body.children[0].type == 'expression_statement':
            first_expr = body.children[0]
            if first_expr.children and first_expr.children[0].type == 'string':
                return _node_text(first_expr.children[0], source).strip('\'"')
        return None
        
    def get_decorators(node):
        decs = []
        sib = node.prev_sibling
        while sib and sib.type == 'decorator':
            decs.append(_node_text(sib, source).strip())
            sib = sib.prev_sibling
        return list(reversed(decs))
        
    def get_calls(node):
        calls = []
        for n in _walk_tree(node, {'call'}):
            func = n.child_by_field_name('function')
            if func:
                calls.append(_node_text(func, source))
        return list(set(calls))

    classes = []
    functions = []
    blocks = []
    
    # Process classes
    for n in _walk_tree(root, {'class_definition'}):
        name_node = n.child_by_field_name('name')
        name = _node_text(name_node, source) if name_node else '?'
        
        superclasses = []
        args = n.child_by_field_name('superclasses')
        if args:
            superclasses = [_node_text(a, source).strip() for a in args.children if a.type == 'argument_list' or a.type not in {'(', ')', ','}]
            
        methods = []
        body = n.child_by_field_name('body')
        if body:
            for m in _walk_tree(body, {'function_definition'}):
                m_name_node = m.child_by_field_name('name')
                m_name = _node_text(m_name_node, source) if m_name_node else '?'
                m_params = m.child_by_field_name('parameters')
                methods.append({
                    'name': m_name,
                    'params': _node_text(m_params, source).strip() if m_params else '()',
                    'docstring': get_docstring(m),
                    'calls': get_calls(m),
                    'line_range': [m.start_point[0] + 1, m.end_point[0] + 1]
                })
                blocks.append({
                    'block_type': 'method',
                    'name': m_name,
                    'parent_name': name,
                    'start_line': m.start_point[0] + 1,
                    'end_line': m.end_point[0] + 1,
                    'content': _node_text(m, source)
                })

        classes.append({
            'name': name,
            'decorators': get_decorators(n),
            'superclasses': [s for s in superclasses if s not in {'(', ')', ','}],
            'docstring': get_docstring(n),
            'methods': methods,
            'line_range': [n.start_point[0] + 1, n.end_point[0] + 1]
        })
        blocks.append({
            'block_type': 'class',
            'name': name,
            'parent_name': None,
            'start_line': n.start_point[0] + 1,
            'end_line': n.end_point[0] + 1,
            'content': _node_text(n, source)
        })

    # Process top-level functions
    for n in _walk_tree(root, {'function_definition'}):
        # Skip if it's inside a class (we already grabbed those as methods)
        parent = n.parent
        is_method = False
        while parent:
            if parent.type == 'class_definition':
                is_method = True
                break
            parent = parent.parent
        if is_method:
            continue
            
        name_node = n.child_by_field_name('name')
        name = _node_text(name_node, source) if name_node else '?'
        ret = n.child_by_field_name('return_type')
        params = n.child_by_field_name('parameters')
        
        functions.append({
            'name': name,
            'params': _node_text(params, source).strip() if params else '()',
            'return_type': _node_text(ret, source).strip() if ret else None,
            'decorators': get_decorators(n),
            'docstring': get_docstring(n),
            'calls': get_calls(n),
            'line_range': [n.start_point[0] + 1, n.end_point[0] + 1]
        })
        blocks.append({
            'block_type': 'function',
            'name': name,
            'parent_name': None,
            'start_line': n.start_point[0] + 1,
            'end_line': n.end_point[0] + 1,
            'content': _node_text(n, source)
        })

    # Module-level block fallback
    if not blocks:
        blocks.append({
            'block_type': 'module_level',
            'name': None,
            'parent_name': None,
            'start_line': 1,
            'end_line': len(source.splitlines()),
            'content': source.decode('utf-8', errors='replace')
        })

    return {'imports': imports, 'classes': classes, 'functions': functions}, blocks

