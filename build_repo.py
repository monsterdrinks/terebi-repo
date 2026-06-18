import os
import hashlib
import zipfile
import xml.etree.ElementTree as ET

def get_addon_version(addon_path):
    tree = ET.parse(os.path.join(addon_path, 'addon.xml'))
    root = tree.getroot()
    return root.get('version')

def create_zip(addon_id, addon_path, version):
    zip_name = f"{addon_id}-{version}.zip"
    zip_path = os.path.join(addon_path, zip_name)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(addon_path):
            if '.git' in root or '__pycache__' in root:
                continue
            for file in files:
                if file.endswith('.zip') or file.endswith('.pyc') or file == 'index.html':
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.join(addon_id, os.path.relpath(file_path, addon_path))
                zipf.write(file_path, arcname)
    return zip_path

def generate_index_html(directory):
    # Generates a simple HTML directory listing so Kodi can browse the repo
    html = "<html>\n<body>\n<h1>Directory listing</h1>\n<hr/>\n<pre>\n"
    html += "<a href=\"../\">../</a>\n"
    
    items = sorted(os.listdir(directory))
    for item in items:
        if item.startswith('.') or item == 'index.html' or item == '__pycache__':
            continue
        
        path = os.path.join(directory, item)
        if os.path.isdir(path):
            html += f"<a href=\"{item}/\">{item}/</a>\n"
        else:
            html += f"<a href=\"{item}\">{item}</a>\n"
            
    html += "</pre>\n</body>\n</html>\n"
    with open(os.path.join(directory, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html)

def build_repo():
    addons = ['plugin.video.terebi', 'repository.terebi']
    addons_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n'
    
    for addon_id in addons:
        addon_path = os.path.join(os.getcwd(), addon_id)
        if not os.path.exists(addon_path):
            print(f"Directory {addon_path} not found.")
            continue
            
        # Read the addon.xml
        xml_path = os.path.join(addon_path, 'addon.xml')
        with open(xml_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
            
        # Remove the xml declaration from individual addon.xml files
        xml_content = xml_content.replace('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n', '')
        addons_xml += xml_content + '\n'
        
        # Create the zip file for the addon
        version = get_addon_version(addon_path)
        zip_path = create_zip(addon_id, addon_path, version)
        print(f"Created {zip_path}")
        
        # Generate index.html for the addon folder
        generate_index_html(addon_path)

    addons_xml += '</addons>\n'
    
    # Save addons.xml
    with open('addons.xml', 'w', encoding='utf-8') as f:
        f.write(addons_xml)
        
    # Generate MD5 hash for addons.xml
    m = hashlib.md5(addons_xml.encode('utf-8')).hexdigest()
    with open('addons.xml.md5', 'w', encoding='utf-8') as f:
        f.write(m)
        
    # Generate index.html for the root folder
    generate_index_html(os.getcwd())
        
    print("addons.xml, MD5, and index.html generated successfully.")

if __name__ == '__main__':
    build_repo()
