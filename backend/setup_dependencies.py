"""
Setup script to check and install all required dependencies
Run: python setup_dependencies.py
"""
import subprocess
import sys
from pathlib import Path

def check_and_install_dependencies():
    """Check and install all required dependencies"""
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ requirements.txt not found!")
        return False
    
    print("=" * 60)
    print("🔧 SprintoBot Dependency Installer")
    print("=" * 60)
    
    print("\n📦 Reading requirements...")
    with open(requirements_file, 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    print(f"   Found {len(requirements)} packages\n")
    
    # Check which packages are missing
    missing_packages = []
    installed_packages = []
    
    for req in requirements:
        package_name = req.split('==')[0].split('[')[0]
        try:
            __import__(package_name.lower().replace('-', '_'))
            installed_packages.append(package_name)
            print(f"✅ {package_name} - installed")
        except ImportError:
            missing_packages.append(req)
            print(f"❌ {package_name} - missing")
    
    if not missing_packages:
        print(f"\n✅ All {len(requirements)} packages are installed!")
        return True
    
    print(f"\n⚠️  {len(missing_packages)} package(s) need to be installed:")
    for pkg in missing_packages:
        print(f"   - {pkg}")
    
    # Ask user if they want to install
    response = input("\n📥 Install missing packages? (y/n): ").lower()
    
    if response == 'y':
        print("\n🚀 Installing packages...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ])
            print("\n✅ All packages installed successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Installation failed: {str(e)}")
            return False
    else:
        print("\n⏭️  Skipping installation")
        print("   To install manually, run:")
        print(f"   pip install -r {requirements_file}")
        return False

def verify_critical_imports():
    """Verify critical imports work"""
    print("\n" + "=" * 60)
    print("🔍 Verifying Critical Imports")
    print("=" * 60 + "\n")
    
    critical_imports = [
        ("fastapi", "FastAPI framework"),
        ("github", "PyGithub (GitHub API)"),
        ("google.genai", "Google Gemini AI"),
        ("pydantic", "Data validation"),
        ("dotenv", "Environment variables")
    ]
    
    all_ok = True
    for module, description in critical_imports:
        try:
            __import__(module)
            print(f"✅ {module:20s} - {description}")
        except ImportError as e:
            print(f"❌ {module:20s} - FAILED: {str(e)}")
            all_ok = False
    
    return all_ok

if __name__ == "__main__":
    print("\n")
    
    # Step 1: Install dependencies
    deps_ok = check_and_install_dependencies()
    
    if deps_ok:
        # Step 2: Verify imports
        imports_ok = verify_critical_imports()
        
        if imports_ok:
            print("\n" + "=" * 60)
            print("✅ Setup Complete! You can now run:")
            print("   python test_with_new_ai.py")
            print("   or")
            print("   uvicorn app.main:app --reload")
            print("=" * 60 + "\n")
        else:
            print("\n" + "=" * 60)
            print("⚠️  Some imports failed. Try reinstalling:")
            print("   pip install -r requirements.txt --force-reinstall")
            print("=" * 60 + "\n")
    else:
        print("\n" + "=" * 60)
        print("❌ Setup incomplete. Please install dependencies manually:")
        print("   pip install -r requirements.txt")
        print("=" * 60 + "\n")
