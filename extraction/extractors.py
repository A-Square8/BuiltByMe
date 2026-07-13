from .ts_parser import parse_code


def _node_text(node, source):
    return source[node.start_byte:node.end_byte].decode('utf-8', errors='replace')


def _walk_tree(node, types):
    results = []
    if node.type in types:
        results.append(node)
    for child in node.children:
        results.extend(_walk_tree(child, types))
    return results


def extract_python(source):
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


def extract_javascript(source):
    tree = parse_code(source, 'javascript')
    if not tree:
        return {}, []
    root = tree.root_node
    blocks = []
    imports = []
    for n in _walk_tree(root, {'import_statement'}):
        imports.append(_node_text(n, source).strip())
    exports = []
    for n in _walk_tree(root, {'export_statement'}):
        text = _node_text(n, source).strip()
        exports.append(text[:100] + '...' if len(text) > 200 else text)
    functions = []
    for n in _walk_tree(root, {'function_declaration', 'arrow_function', 'function'}):
        name_node = n.child_by_field_name('name')
        params = n.child_by_field_name('parameters')
        name = _node_text(name_node, source) if name_node else 'anonymous'
        if n.parent and n.parent.type == 'variable_declarator':
            pname = n.parent.child_by_field_name('name')
            if pname:
                name = _node_text(pname, source)
        functions.append({'name': name, 'params': _node_text(params, source).strip() if params else '()'})
        blocks.append({'block_type': 'function', 'name': name, 'parent_name': None,
                        'start_line': n.start_point[0]+1, 'end_line': n.end_point[0]+1, 'content': _node_text(n, source)})
    classes = []
    for n in _walk_tree(root, {'class_declaration'}):
        name_node = n.child_by_field_name('name')
        cname = _node_text(name_node, source) if name_node else '?'
        classes.append({'name': cname})
        blocks.append({'block_type': 'class', 'name': cname, 'parent_name': None,
                        'start_line': n.start_point[0]+1, 'end_line': n.end_point[0]+1, 'content': _node_text(n, source)})
        body = n.child_by_field_name('body')
        if body:
            for m in _walk_tree(body, {'method_definition'}):
                mn = m.child_by_field_name('name')
                mname = _node_text(mn, source) if mn else '?'
                blocks.append({'block_type': 'method', 'name': mname, 'parent_name': cname,
                                'start_line': m.start_point[0]+1, 'end_line': m.end_point[0]+1, 'content': _node_text(m, source)})
    if not blocks:
        blocks.append({'block_type': 'module_level', 'name': None, 'parent_name': None,
                        'start_line': 1, 'end_line': len(source.splitlines()), 'content': source.decode('utf-8', errors='replace')})
    return {'imports': imports, 'exports': exports, 'functions': functions, 'classes': classes}, blocks


def extract_typescript(source):
    tree = parse_code(source, 'typescript')
    if not tree:
        return extract_javascript(source)
    root = tree.root_node
    blocks = []
    imports = [_node_text(n, source).strip() for n in _walk_tree(root, {'import_statement'})]
    exports = [_node_text(n, source).strip()[:150] for n in _walk_tree(root, {'export_statement'})]
    functions = []
    for n in _walk_tree(root, {'function_declaration', 'arrow_function'}):
        name_node = n.child_by_field_name('name')
        params = n.child_by_field_name('parameters')
        ret = n.child_by_field_name('return_type')
        name = _node_text(name_node, source) if name_node else 'anonymous'
        if n.parent and n.parent.type == 'variable_declarator':
            pname = n.parent.child_by_field_name('name')
            if pname: name = _node_text(pname, source)
        functions.append({'name': name, 'params': _node_text(params, source).strip() if params else '()',
                          'return_type': _node_text(ret, source).strip() if ret else None})
        blocks.append({'block_type': 'function', 'name': name, 'parent_name': None,
                        'start_line': n.start_point[0]+1, 'end_line': n.end_point[0]+1, 'content': _node_text(n, source)})
    classes = []
    for n in _walk_tree(root, {'class_declaration'}):
        name_node = n.child_by_field_name('name')
        cname = _node_text(name_node, source) if name_node else '?'
        classes.append({'name': cname})
        blocks.append({'block_type': 'class', 'name': cname, 'parent_name': None,
                        'start_line': n.start_point[0]+1, 'end_line': n.end_point[0]+1, 'content': _node_text(n, source)})
        body = n.child_by_field_name('body')
        if body:
            for m in _walk_tree(body, {'method_definition', 'public_field_definition'}):
                mn = m.child_by_field_name('name')
                mname = _node_text(mn, source) if mn else '?'
                blocks.append({'block_type': 'method', 'name': mname, 'parent_name': cname,
                                'start_line': m.start_point[0]+1, 'end_line': m.end_point[0]+1, 'content': _node_text(m, source)})
    interfaces = []
    for n in _walk_tree(root, {'interface_declaration'}):
        name_node = n.child_by_field_name('name')
        iname = _node_text(name_node, source) if name_node else '?'
        interfaces.append({'name': iname})
        blocks.append({'block_type': 'class', 'name': iname, 'parent_name': None,
                        'start_line': n.start_point[0]+1, 'end_line': n.end_point[0]+1, 'content': _node_text(n, source)})
    if not blocks:
        blocks.append({'block_type': 'module_level', 'name': None, 'parent_name': None,
                        'start_line': 1, 'end_line': len(source.splitlines()), 'content': source.decode('utf-8', errors='replace')})
    return {'imports': imports, 'exports': exports, 'functions': functions, 'classes': classes, 'interfaces': interfaces}, blocks


def extract_java(source):
    tree = parse_code(source, 'java')
    if not tree:
        return {}
    root = tree.root_node
    blocks = []
    imports = [_node_text(n, source).strip() for n in _walk_tree(root, {'import_declaration'})]
    classes = []
    for n in _walk_tree(root, {'class_declaration', 'interface_declaration', 'enum_declaration'}):
        name_node = n.child_by_field_name('name')
        cname = _node_text(name_node, source) if name_node else '?'
        superclass = n.child_by_field_name('superclass')
        interfaces_node = n.child_by_field_name('interfaces')
        annotations = []
        if n.prev_sibling and n.prev_sibling.type in ('marker_annotation', 'annotation'):
            annotations.append(_node_text(n.prev_sibling, source).strip())
        classes.append({'name': cname,
            'extends': _node_text(superclass, source).strip() if superclass else None,
            'implements': _node_text(interfaces_node, source).strip() if interfaces_node else None,
            'annotations': annotations})
        blocks.append({'block_type': 'class', 'name': cname, 'parent_name': None,
                        'start_line': n.start_point[0]+1, 'end_line': n.end_point[0]+1, 'content': _node_text(n, source)})
        body = n.child_by_field_name('body')
        if body:
            for m in _walk_tree(body, {'method_declaration', 'constructor_declaration'}):
                mn = m.child_by_field_name('name')
                mname = _node_text(mn, source) if mn else '?'
                blocks.append({'block_type': 'method', 'name': mname, 'parent_name': cname,
                                'start_line': m.start_point[0]+1, 'end_line': m.end_point[0]+1, 'content': _node_text(m, source)})
    methods = []
    for n in _walk_tree(root, {'method_declaration', 'constructor_declaration'}):
        name_node = n.child_by_field_name('name')
        params = n.child_by_field_name('parameters')
        ret = n.child_by_field_name('type')
        methods.append({'name': _node_text(name_node, source) if name_node else '?',
            'params': _node_text(params, source).strip() if params else '()',
            'return_type': _node_text(ret, source).strip() if ret else None})
    if not blocks:
        blocks.append({'block_type': 'module_level', 'name': None, 'parent_name': None,
                        'start_line': 1, 'end_line': len(source.splitlines()), 'content': source.decode('utf-8', errors='replace')})
    return {'imports': imports, 'classes': classes, 'methods': methods}, blocks


def extract_c_cpp(source, lang='c'):
    tree = parse_code(source, lang)
    if not tree:
        return {}, []
    root = tree.root_node
    blocks = []
    includes = [_node_text(n, source).strip() for n in _walk_tree(root, {'preproc_include'})]
    functions = []
    for n in _walk_tree(root, {'function_definition'}):
        declarator = n.child_by_field_name('declarator')
        ret = n.child_by_field_name('type')
        name = '?'
        if declarator:
            fn_decl = declarator
            while fn_decl and fn_decl.type != 'function_declarator' and fn_decl.children:
                for c in fn_decl.children:
                    if c.type == 'function_declarator':
                        fn_decl = c
                        break
                else:
                    break
            if fn_decl and fn_decl.type == 'function_declarator':
                dn = fn_decl.child_by_field_name('declarator')
                if dn:
                    name = _node_text(dn, source)
        functions.append({'name': name, 'return_type': _node_text(ret, source).strip() if ret else None})
        blocks.append({'block_type': 'function', 'name': name, 'parent_name': None,
                        'start_line': n.start_point[0]+1, 'end_line': n.end_point[0]+1, 'content': _node_text(n, source)})
    structs = []
    for n in _walk_tree(root, {'struct_specifier'}):
        name_node = n.child_by_field_name('name')
        sname = _node_text(name_node, source) if name_node else 'anonymous'
        structs.append({'name': sname})
        blocks.append({'block_type': 'class', 'name': sname, 'parent_name': None,
                        'start_line': n.start_point[0]+1, 'end_line': n.end_point[0]+1, 'content': _node_text(n, source)})
    classes = []
    if lang == 'cpp':
        for n in _walk_tree(root, {'class_specifier'}):
            name_node = n.child_by_field_name('name')
            cname = _node_text(name_node, source) if name_node else '?'
            classes.append({'name': cname})
            blocks.append({'block_type': 'class', 'name': cname, 'parent_name': None,
                            'start_line': n.start_point[0]+1, 'end_line': n.end_point[0]+1, 'content': _node_text(n, source)})
    if not blocks:
        blocks.append({'block_type': 'module_level', 'name': None, 'parent_name': None,
                        'start_line': 1, 'end_line': len(source.splitlines()), 'content': source.decode('utf-8', errors='replace')})
    result = {'includes': includes, 'functions': functions, 'structs': structs}
    if classes:
        result['classes'] = classes
    return result, blocks


def extract_go(source):
    tree = parse_code(source, 'go')
    if not tree:
        return {}, []
    root = tree.root_node
    blocks = []
    imports = []
    for n in _walk_tree(root, {'import_declaration', 'import_spec'}):
        text = _node_text(n, source).strip()
        imports.append(text if text.startswith('import') else f'import {text}')
    functions = []
    for n in _walk_tree(root, {'function_declaration', 'method_declaration'}):
        name_node = n.child_by_field_name('name')
        params = n.child_by_field_name('parameters')
        result = n.child_by_field_name('result')
        fname = _node_text(name_node, source) if name_node else '?'
        functions.append({'name': fname, 'params': _node_text(params, source).strip() if params else '()',
            'return_type': _node_text(result, source).strip() if result else None})
        blocks.append({'block_type': 'function', 'name': fname, 'parent_name': None,
                        'start_line': n.start_point[0]+1, 'end_line': n.end_point[0]+1, 'content': _node_text(n, source)})
    structs = []
    for n in _walk_tree(root, {'type_declaration'}):
        for c in n.children:
            if c.type == 'type_spec':
                name_node = c.child_by_field_name('name')
                type_node = c.child_by_field_name('type')
                kind = type_node.type if type_node else 'unknown'
                sname = _node_text(name_node, source) if name_node else '?'
                structs.append({'name': sname, 'kind': kind})
                blocks.append({'block_type': 'class', 'name': sname, 'parent_name': None,
                                'start_line': c.start_point[0]+1, 'end_line': c.end_point[0]+1, 'content': _node_text(c, source)})
    if not blocks:
        blocks.append({'block_type': 'module_level', 'name': None, 'parent_name': None,
                        'start_line': 1, 'end_line': len(source.splitlines()), 'content': source.decode('utf-8', errors='replace')})
    return {'imports': imports, 'functions': functions, 'types': structs}, blocks


def extract_rust(source):
    tree = parse_code(source, 'rust')
    if not tree:
        return {}, []
    root = tree.root_node
    blocks = []
    uses = [_node_text(n, source).strip() for n in _walk_tree(root, {'use_declaration'})]
    functions = []
    for n in _walk_tree(root, {'function_item'}):
        name_node = n.child_by_field_name('name')
        params = n.child_by_field_name('parameters')
        ret = n.child_by_field_name('return_type')
        fname = _node_text(name_node, source) if name_node else '?'
        functions.append({'name': fname, 'params': _node_text(params, source).strip() if params else '()',
            'return_type': _node_text(ret, source).strip() if ret else None})
        blocks.append({'block_type': 'function', 'name': fname, 'parent_name': None,
                        'start_line': n.start_point[0]+1, 'end_line': n.end_point[0]+1, 'content': _node_text(n, source)})
    structs = []
    for n in _walk_tree(root, {'struct_item'}):
        name_node = n.child_by_field_name('name')
        sname = _node_text(name_node, source) if name_node else '?'
        structs.append({'name': sname})
        blocks.append({'block_type': 'class', 'name': sname, 'parent_name': None,
                        'start_line': n.start_point[0]+1, 'end_line': n.end_point[0]+1, 'content': _node_text(n, source)})
    impls = []
    for n in _walk_tree(root, {'impl_item'}):
        name_node = n.child_by_field_name('type')
        trait_node = n.child_by_field_name('trait')
        impl_name = _node_text(name_node, source) if name_node else '?'
        impls.append({'type': impl_name, 'trait': _node_text(trait_node, source).strip() if trait_node else None})
        blocks.append({'block_type': 'class', 'name': f'impl {impl_name}', 'parent_name': None,
                        'start_line': n.start_point[0]+1, 'end_line': n.end_point[0]+1, 'content': _node_text(n, source)})
        # Extract methods inside impl blocks
        body = n.child_by_field_name('body')
        if body:
            for m in _walk_tree(body, {'function_item'}):
                mn = m.child_by_field_name('name')
                mname = _node_text(mn, source) if mn else '?'
                blocks.append({'block_type': 'method', 'name': mname, 'parent_name': impl_name,
                                'start_line': m.start_point[0]+1, 'end_line': m.end_point[0]+1, 'content': _node_text(m, source)})
    if not blocks:
        blocks.append({'block_type': 'module_level', 'name': None, 'parent_name': None,
                        'start_line': 1, 'end_line': len(source.splitlines()), 'content': source.decode('utf-8', errors='replace')})
    return {'uses': uses, 'functions': functions, 'structs': structs, 'impls': impls}, blocks


def extract_html(source):
    tree = parse_code(source, 'html')
    if not tree:
        return {}
    root = tree.root_node
    text = source.decode('utf-8', errors='replace')
    result = {'scripts': [], 'links': [], 'meta': []}
    for n in _walk_tree(root, {'element'}):
        start_tag = None
        for c in n.children:
            if c.type == 'start_tag':
                start_tag = c
                break
        if not start_tag:
            continue
        tag_name = None
        for c in start_tag.children:
            if c.type == 'tag_name':
                tag_name = _node_text(c, source).lower()
                break
        if not tag_name:
            continue
        if tag_name == 'script':
            attrs = {}
            for c in start_tag.children:
                if c.type == 'attribute':
                    aname = c.child_by_field_name('name')
                    aval = c.child_by_field_name('value')
                    if aname:
                        attrs[_node_text(aname, source)] = _node_text(aval, source).strip('"\'') if aval else ''
            result['scripts'].append(attrs)
        elif tag_name == 'link':
            attrs = {}
            for c in start_tag.children:
                if c.type == 'attribute':
                    aname = c.child_by_field_name('name')
                    aval = c.child_by_field_name('value')
                    if aname:
                        attrs[_node_text(aname, source)] = _node_text(aval, source).strip('"\'') if aval else ''
            result['links'].append(attrs)
        elif tag_name == 'meta':
            attrs = {}
            for c in start_tag.children:
                if c.type == 'attribute':
                    aname = c.child_by_field_name('name')
                    aval = c.child_by_field_name('value')
                    if aname:
                        attrs[_node_text(aname, source)] = _node_text(aval, source).strip('"\'') if aval else ''
            result['meta'].append(attrs)
    return result


def extract_css(source):
    tree = parse_code(source, 'css')
    if not tree:
        return {}
    root = tree.root_node
    selectors = set()
    for n in _walk_tree(root, {'class_selector'}):
        selectors.add(_node_text(n, source).strip())
    variables = []
    for n in _walk_tree(root, {'declaration'}):
        prop = n.child_by_field_name('property')
        if prop and _node_text(prop, source).startswith('--'):
            variables.append(_node_text(prop, source))
    media = []
    for n in _walk_tree(root, {'media_statement'}):
        text = _node_text(n, source)
        idx = text.find('{')
        if idx > 0:
            media.append(text[:idx].strip())
    return {'classes': list(selectors)[:50], 'variables': variables[:30], 'media_queries': media[:10]}


def extract_generic(source, lang_name):
    tree = parse_code(source, lang_name)
    if not tree:
        return {}, []
    root = tree.root_node
    import_types = {'import_statement', 'import_declaration', 'import_from_statement', 'use_declaration', 'preproc_include', 'import_spec', 'import_header', 'import_directive'}
    func_types = {'function_definition', 'function_declaration', 'method_declaration', 'function_item', 'arrow_function', 'function_item'}
    class_types = {'class_definition', 'class_declaration', 'class_specifier', 'struct_specifier', 'struct_item', 'interface_declaration', 'object_declaration', 'companion_object', 'enum_declaration'}
    blocks = []
    imports = [_node_text(n, source).strip() for n in _walk_tree(root, import_types)]
    functions = []
    for n in _walk_tree(root, func_types):
        name_node = n.child_by_field_name('name')
        name = _node_text(name_node, source) if name_node else 'anonymous'
        functions.append(name)
        blocks.append({
            'block_type': 'function',
            'name': name,
            'parent_name': None,
            'start_line': n.start_point[0] + 1,
            'end_line': n.end_point[0] + 1,
            'content': _node_text(n, source)
        })
    classes = []
    for n in _walk_tree(root, class_types):
        name_node = n.child_by_field_name('name')
        name = _node_text(name_node, source) if name_node else 'anonymous'
        classes.append(name)
        blocks.append({
            'block_type': 'class',
            'name': name,
            'parent_name': None,
            'start_line': n.start_point[0] + 1,
            'end_line': n.end_point[0] + 1,
            'content': _node_text(n, source)
        })
        
    if not blocks:
        blocks.append({
            'block_type': 'module_level',
            'name': None,
            'parent_name': None,
            'start_line': 1,
            'end_line': len(source.splitlines()),
            'content': source.decode('utf-8', errors='replace')
        })
    return {'imports': imports, 'functions': functions, 'classes': classes}, blocks


def extract_kotlin(source):
    tree = parse_code(source, 'kotlin')
    if not tree:
        return {}, []
    root = tree.root_node
    blocks = []
    imports = []
    for n in _walk_tree(root, {'import_header'}):
        imports.append(_node_text(n, source).strip())
    functions = []
    for n in _walk_tree(root, {'function_declaration'}):
        name_node = n.child_by_field_name('identifier') or n.child_by_field_name('name')
        fname = _node_text(name_node, source) if name_node else '?'
        functions.append({'name': fname})
        blocks.append({'block_type': 'function', 'name': fname, 'parent_name': None,
                        'start_line': n.start_point[0]+1, 'end_line': n.end_point[0]+1, 'content': _node_text(n, source)})
    classes = []
    for n in _walk_tree(root, {'class_declaration', 'object_declaration', 'companion_object'}):
        name_node = n.child_by_field_name('identifier') or n.child_by_field_name('name')
        cname = _node_text(name_node, source) if name_node else '?'
        classes.append({'name': cname})
        blocks.append({'block_type': 'class', 'name': cname, 'parent_name': None,
                        'start_line': n.start_point[0]+1, 'end_line': n.end_point[0]+1, 'content': _node_text(n, source)})
        body = n.child_by_field_name('body') or n.child_by_field_name('class_body')
        if body:
            for m in _walk_tree(body, {'function_declaration'}):
                mn = m.child_by_field_name('identifier') or m.child_by_field_name('name')
                mname = _node_text(mn, source) if mn else '?'
                blocks.append({'block_type': 'method', 'name': mname, 'parent_name': cname,
                                'start_line': m.start_point[0]+1, 'end_line': m.end_point[0]+1, 'content': _node_text(m, source)})
    if not blocks:
        blocks.append({'block_type': 'module_level', 'name': None, 'parent_name': None,
                        'start_line': 1, 'end_line': len(source.splitlines()), 'content': source.decode('utf-8', errors='replace')})
    return {'imports': imports, 'functions': functions, 'classes': classes}, blocks

EXTRACTORS = {
    'python': extract_python,
    'javascript': extract_javascript,
    'typescript': extract_typescript,
    'java': extract_java,
    'c': lambda s: extract_c_cpp(s, 'c'),
    'cpp': lambda s: extract_c_cpp(s, 'cpp'),
    'go': extract_go,
    'rust': extract_rust,
    'html': extract_html,
    'css': extract_css,
    'kotlin': extract_kotlin,
}


def extract_file(source_bytes, language):
    extractor = EXTRACTORS.get(language)
    metadata = {}
    if extractor:
        metadata = extractor(source_bytes)
    else:
        return extract_generic(source_bytes, language)
        
    if isinstance(metadata, tuple) and len(metadata) == 2:
        return metadata
        
    _, blocks = extract_generic(source_bytes, language)
    return metadata, blocks
