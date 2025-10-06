# UAV Flying Wing Design Automation

A comprehensive CATIA V5 automation system for creating parametric UAV flying wing designs using PyCATIA.

## 🎯 Project Overview

This project provides a complete 29-step automated workflow for designing UAV flying wings in CATIA V5, featuring:
- **Parametric Design**: Database-driven parameter management
- **Modular Architecture**: Individual functions for each design step
- **CATIA Integration**: Full PyCATIA automation for complex geometry creation
- **Database Management**: SQLite database for design templates and parameters

## 🏗️ Project Structure

```
├── uav_wing_design.py          # Main UAV wing creation script (29 individual steps)
├── py.py                       # Alternative modular implementation
├── design_db_schema.py         # Database schema and population script
├── uav_wing.py                 # Design data definitions and templates
├── design.db                   # SQLite database with design data
├── design_old.db              # Optimized database version
├── steps.xlsx                 # Excel export of design steps and parameters
├── export_to_excel.py         # Database to Excel export utility
└── README.md                  # Project documentation
```

## 🚀 Features

### **Automated Wing Creation**
- **29 Individual Steps**: Each design operation as a separate function
- **Complete Workflow**: From CATIA initialization to final wing geometry
- **Error Handling**: Comprehensive exception management
- **Progress Tracking**: Step-by-step execution feedback

### **Database-Driven Design**
- **Design Templates**: Structured wing design definitions
- **Parameter Management**: 12 key design parameters with validation
- **Step Documentation**: Complete step-by-step instructions
- **Excel Integration**: Export capabilities for documentation

### **Key Design Operations**
- CATIA Environment Setup
- Reference Plane and Axis Definition
- Parametric Point and Spline Creation
- Multi-Section Surface Lofting
- Surface Joining and Solid Creation
- Wing Mirroring for Full Wingspan
- Visibility Control for Clean Display

## 🛠️ Requirements

### **Software Dependencies**
- **CATIA V5** (R20 or higher recommended)
- **Python 3.8+**
- **PyCATIA library**

### **Python Dependencies**
```bash
pip install pycatia
pip install sqlite3  # (built-in with Python)
pip install pandas   # (for Excel export)
pip install openpyxl # (for Excel export)
```

## 🎮 Usage

### **Basic Wing Creation**
```python
from uav_wing_design import create_flying_wing

# Create complete UAV wing
wing_part = create_flying_wing()
if wing_part:
    print("Successfully created flying wing UAV model")
```

### **Individual Step Execution**
```python
# Execute individual steps for testing/debugging
catia_objects = step_01_initialize_catia_app()
hybrid_objects = step_02_setup_hybrid_shape_environment(catia_objects['part'])
# ... continue with specific steps as needed
```

### **Database Management**
```python
# Create/populate database
python design_db_schema.py

# Export to Excel
python export_to_excel.py
```

## 📊 Design Parameters

The system includes 12 key parametric values:

| Parameter | Default | Unit | Description |
|-----------|---------|------|-------------|
| `construction_plane_offset` | 500.0 | mm | Wing plane offset from origin |
| `root_point_h` | -250.0 | mm | Root chord horizontal position |
| `tip_offset_yz` | 300.0 | mm | Tip chord YZ offset |
| `spline_tension_1` | 0.5 | - | Root spline tension control |
| `spline_tension_2` | 0.3 | - | Tip spline tension control |
| `sweep_angle` | -30.0 | deg | Wing sweep angle |
| `wing_thickness` | 10.0 | mm | Final wing thickness |
| ... | ... | ... | ... |

## 🔧 Development

### **Architecture**
- **Modular Functions**: Each step is independently testable
- **Clean Interfaces**: Clear parameter passing between functions
- **Error Recovery**: Graceful handling of CATIA API failures
- **Database Integration**: Complete parameter and step management

### **Testing**
```python
# Test individual steps
python -c "from uav_wing_design import step_01_initialize_catia_app; print('✅ Step 1 OK')"

# Full workflow test
python uav_wing_design.py
```

## 📈 Future Enhancements

- [ ] GUI Parameter Interface
- [ ] Batch Design Generation
- [ ] CAD File Export (STEP, IGES)
- [ ] Advanced Wing Configurations
- [ ] Optimization Integration
- [ ] Unit Test Framework

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **PyCATIA Community** for the excellent CATIA automation library
- **CATIA V5** for the robust CAD platform
- **UAV Design Community** for inspiration and requirements

---

**Note**: This project requires CATIA V5 installation and appropriate licensing for full functionality.