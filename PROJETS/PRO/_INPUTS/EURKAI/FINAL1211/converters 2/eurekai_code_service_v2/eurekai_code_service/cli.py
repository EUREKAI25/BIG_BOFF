#!/usr/bin/env python3
"""
EUREKAI Code Service - CLI
Audit et conversion de scripts JavaScript
"""
import argparse
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from eurekai_audit import audit_file, parse_js_file, analyze, generate_report
from eurekai_convert import convert_file

def cmd_audit(args):
    """Commande audit"""
    report = audit_file(args.file, format=args.format)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ Rapport sauvegardé: {args.output}")
    else:
        print(report)

def cmd_convert(args):
    """Commande convert"""
    result = convert_file(
        filepath=args.file,
        output_dir=args.output,
        port=args.port
    )
    
    print(f"✅ Module '{result['module_name']}' généré!")
    print(f"📁 Répertoire: {result['output_dir']}")
    print(f"📊 Score: {result['analysis'].score}/100")
    print("\nFichiers générés:")
    for name, path in result['files'].items():
        print(f"  - {name}")
    
    print(f"\n🚀 Pour démarrer:")
    print(f"   cd {result['output_dir']}")
    print(f"   npm install")
    print(f"   npm start")

def cmd_info(args):
    """Commande info - affiche les infos extraites"""
    parsed = parse_js_file(args.file)
    
    print(f"📄 Fichier: {args.file}")
    print(f"\n📦 Fonctions détectées: {len(parsed.functions)}")
    
    for f in parsed.functions:
        exported = "✓" if f.is_exported else "✗"
        callback = "🔄" if f.has_callback else ""
        params = ', '.join([p.name for p in f.params])
        print(f"  [{exported}] {f.name}({params}) {callback}")
        
        if f.options_schema:
            print(f"      Options: {list(f.options_schema.keys())}")
    
    if parsed.globals_read:
        print(f"\n🔗 Dépendances externes: {', '.join(parsed.globals_read)}")
    
    if parsed.globals_written:
        print(f"📤 Exports: {', '.join(parsed.globals_written)}")

def main():
    parser = argparse.ArgumentParser(
        description='EUREKAI Code Service - Audit et conversion JS → Python',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  eurekai audit traverse.js                    # Audit avec rapport YAML
  eurekai audit traverse.js -f markdown        # Rapport Markdown
  eurekai convert traverse.js -o ./out         # Conversion complète
  eurekai info traverse.js                     # Infos rapides
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commandes disponibles')
    
    # Commande audit
    audit_parser = subparsers.add_parser('audit', help='Analyser un fichier JS')
    audit_parser.add_argument('file', help='Fichier JS à analyser')
    audit_parser.add_argument('-f', '--format', choices=['yaml', 'json', 'markdown', 'md'],
                             default='yaml', help='Format du rapport')
    audit_parser.add_argument('-o', '--output', help='Fichier de sortie (défaut: stdout)')
    audit_parser.set_defaults(func=cmd_audit)
    
    # Commande convert
    convert_parser = subparsers.add_parser('convert', help='Convertir un fichier JS')
    convert_parser.add_argument('file', help='Fichier JS à convertir')
    convert_parser.add_argument('-o', '--output', help='Répertoire de sortie')
    convert_parser.add_argument('-p', '--port', type=int, default=3000,
                               help='Port du serveur (défaut: 3000)')
    convert_parser.set_defaults(func=cmd_convert)
    
    # Commande info
    info_parser = subparsers.add_parser('info', help='Afficher les infos extraites')
    info_parser.add_argument('file', help='Fichier JS à analyser')
    info_parser.set_defaults(func=cmd_info)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        args.func(args)
    except FileNotFoundError as e:
        print(f"❌ Fichier non trouvé: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
