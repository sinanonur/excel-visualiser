# Quick Start Guide

## 🚀 One-Command Installation

### Linux
```bash
chmod +x install-linux.sh && ./install-linux.sh
```

### macOS  
```bash
chmod +x install-macos.sh && ./install-macos.sh
```

### Windows
**Option 1 (Recommended):** Double-click `install-windows.bat`

**Option 2:** In PowerShell:
```powershell
.\install-windows.ps1
```

## ▶️ Starting the Application

| Platform | Command |
|----------|---------|
| **Linux/macOS** | `./run.sh start` |
| **Windows** | Double-click `run.bat` |

## 🌐 Access the Application

Once started, open your browser to:
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:5001

The browser should open automatically!

## 📊 Try It Out

1. **Upload Sample Data**: Use the included `test_data.xlsx` file
2. **Explore Data**: Navigate through the tabs:
   - **Data Preview**: See your data
   - **Column Management**: Adjust data types
   - **Filters**: Apply data filters
   - **Visualizations**: Create interactive plots

## ⚠️ Troubleshooting

### Common Issues

**"Command not found" errors:**
- Make sure Python 3.7+ and Node.js 14+ are installed
- Check that they're added to your system PATH

**Port already in use:**
- Stop any existing servers using ports 3000 or 5001
- Use `./run.sh stop` (Linux/macOS) or close terminal windows (Windows)

**Permission errors:**
- Linux/macOS: Run `chmod +x install-*.sh` first
- Windows: Run as Administrator if needed

### Get Help

- 📖 **Full Installation Guide**: See [INSTALLATION.md](INSTALLATION.md)
- 📋 **System Requirements**: Python 3.7+, Node.js 14+, 4GB RAM
- 🔧 **Manual Setup**: Follow platform-specific instructions in INSTALLATION.md

## 🛑 Stopping the Application

| Platform | Command |
|----------|---------|
| **Linux/macOS** | `./run.sh stop` |
| **Windows** | `.\run.ps1 stop` or close the windows |

---

**Need more details?** Check the complete [INSTALLATION.md](INSTALLATION.md) guide.