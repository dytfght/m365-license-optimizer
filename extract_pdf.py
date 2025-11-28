#!/usr/bin/env python3
"""Extract text content from PDF file"""

try:
    import PyPDF2
    
    def extract_pdf_text(pdf_path):
        """Extract text from PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text += f"\n--- Page {page_num + 1} ---\n"
                    text += page.extract_text()
                    
                return text
        except Exception as e:
            return f"Error reading PDF: {e}"
    
    # Extraction du PDF
    pdf_path = "docs/Spécification fonctionnelle V1.1.pdf"
    content = extract_pdf_text(pdf_path)
    
    # Sauvegarder le contenu
    with open("docs/specification_v1.1_extracted.txt", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("✅ PDF extracté avec succès")
    print(f"📊 Nombre de caractères: {len(content)}")
    print("\n📝 Contenu du Lot 7 (premières lignes):")
    
    # Chercher le contenu du Lot 7
    lines = content.split('\n')
    in_lot7 = False
    lot7_content = []
    
    for line in lines:
        if "Lot 7" in line or "LOT 7" in line:
            in_lot7 = True
        if in_lot7:
            lot7_content.append(line)
            if len(lot7_content) > 50:  # Limiter pour l'affichage
                break
    
    if lot7_content:
        print("\n".join(lot7_content[:30]))
    else:
        print("Lot 7 non trouvé dans les 30 premières lignes")

except ImportError:
    print("❌ PyPDF2 non installé. Installation...")
    import subprocess
    subprocess.run(["pip", "install", "PyPDF2"])
    print("✅ PyPDF2 installé. Veuillez relancer le script.")