from tree_sitter import Language, Parser

_LANG_CACHE = {}


def _load_language(lang_name):
    if lang_name in _LANG_CACHE:
        return _LANG_CACHE[lang_name]

    lang_obj = None
    try:
        if lang_name == 'python':
            import tree_sitter_python as mod
            lang_obj = Language(mod.language())
        elif lang_name == 'javascript':
            import tree_sitter_javascript as mod
            lang_obj = Language(mod.language())
        elif lang_name == 'typescript':
            import tree_sitter_typescript as mod
            lang_obj = Language(mod.language_typescript())
        elif lang_name == 'java':
            import tree_sitter_java as mod
            lang_obj = Language(mod.language())
        elif lang_name == 'c':
            import tree_sitter_c as mod
            lang_obj = Language(mod.language())
        elif lang_name == 'cpp':
            import tree_sitter_cpp as mod
            lang_obj = Language(mod.language())
        elif lang_name == 'csharp':
            import tree_sitter_c_sharp as mod
            lang_obj = Language(mod.language())
        elif lang_name == 'go':
            import tree_sitter_go as mod
            lang_obj = Language(mod.language())
        elif lang_name == 'rust':
            import tree_sitter_rust as mod
            lang_obj = Language(mod.language())
        elif lang_name == 'ruby':
            import tree_sitter_ruby as mod
            lang_obj = Language(mod.language())
        elif lang_name == 'php':
            import tree_sitter_php as mod
            lang_obj = Language(mod.language_php())
        elif lang_name == 'html':
            import tree_sitter_html as mod
            lang_obj = Language(mod.language())
        elif lang_name == 'css':
            import tree_sitter_css as mod
            lang_obj = Language(mod.language())
        elif lang_name == 'kotlin':
            import tree_sitter_kotlin as mod
            lang_obj = Language(mod.language())
        elif lang_name == 'json':
            import tree_sitter_json as mod
            lang_obj = Language(mod.language())
    except Exception:
        return None

    if lang_obj:
        _LANG_CACHE[lang_name] = lang_obj
    return lang_obj


def get_parser(lang_name):
    lang = _load_language(lang_name)
    if not lang:
        return None
    parser = Parser(lang)
    return parser


def parse_code(code_bytes, lang_name):
    parser = get_parser(lang_name)
    if not parser:
        return None
    tree = parser.parse(code_bytes)
    return tree
