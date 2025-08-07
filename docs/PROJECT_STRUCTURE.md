# 🗂️ Nigerian E-commerce Customer Support Agent - Project Structure

## 📁 Directory Organization

Following Python best practices from the [Python Packaging Guide](https://docs.python-guide.org/writing/structure/), our project is now professionally organized:

```
customer_support_agent/
├── 📁 src/                     # Main application source code
│   ├── __init__.py
│   └── [Streamlit app and core modules]
├── 📁 config/                  # Configuration management
│   ├── __init__.py
│   └── database_config.py      # Database connection & config
├── 📁 scripts/                 # Utility and data generation scripts
│   ├── generate_bulk_data_ethnically_authentic.py
│   ├── check_ethnic_distribution.py
│   └── clean_and_regenerate_data.py  # 🆕 New clean regeneration script
├── 📁 database/                # Database-related files
│   ├── database_schema.sql     # PostgreSQL schema definition
│   ├── setup_database.py       # Initial database setup
│   ├── add_orders.py           # Order insertion utilities
│   ├── add_remaining_customers.py # Customer utilities
│   ├── simple_fix.py           # Database fixes
│   ├── run_fix.py              # Fix execution
│   └── fix_database.sql        # SQL fixes
├── 📁 docs/                    # Documentation
│   ├── README.md               # Main project documentation
│   ├── DATABASE_README.md      # Database setup guide
│   ├── DATABASE_GUIDE.md       # Database usage guide
│   ├── ETHNIC_AUTHENTICITY_DOCUMENTATION.md  # Cultural authenticity guide
│   └── PROJECT_STRUCTURE.md    # This file
├── 📄 requirements.txt         # Python dependencies
├── 📄 .env_example             # Environment variables template
├── 📄 .gitignore              # Git ignore patterns
├── 📄 deploy.ps1              # Deployment script
└── 📄 .secrets.baseline       # Security baseline
```

## 🎯 Key Improvements

### ✅ **Clean Separation of Concerns**
- **`src/`** - Core application logic
- **`config/`** - Configuration management
- **`scripts/`** - Data operations and utilities
- **`database/`** - Database schema and setup
- **`docs/`** - All documentation centralized

### ✅ **Professional Import Structure**
```python
# From root scripts, import config correctly
sys.path.append(str(Path(__file__).parent.parent))
from config.database_config import DATABASE_CONFIG

# From database scripts
sys.path.append(str(Path(__file__).parent.parent))
from config.database_config import get_repositories
```

### ✅ **Maintainable Documentation**
- All `.md` files centralized in `docs/`
- Clear naming conventions
- Comprehensive guides for each component

## 🚀 **New Enhanced Scripts**

### **scripts/clean_and_regenerate_data.py** 🆕
**Purpose:** Professional database cleanup and regeneration
**Features:**
- ✅ Complete database cleaning while preserving schema
- ✅ Realistic timestamp distribution (fixes "same timestamp" issue)
- ✅ Ethnic authenticity maintained
- ✅ Business logic tier assignment
- ✅ Seasonal shopping patterns
- ✅ Business hours order placement
- ✅ Customer lifetime order distribution

**Usage:**
```bash
cd customer_support_agent
python scripts/clean_and_regenerate_data.py
```

### **scripts/check_ethnic_distribution.py**
**Purpose:** Verify cultural authenticity of generated data
**Features:**
- ✅ Ethnic distribution verification
- ✅ Name-state-ethnicity mapping checks
- ✅ Tier distribution analysis

## 📊 **Enhanced Data Generation Features**

### **🕐 Realistic Timestamp Distribution**
```python
# Business growth periods
periods = {
    'early_stage': 3 years ago → 2 years ago (15% weight)
    'growth_stage': 2 years ago → 1 year ago (25% weight)
    'expansion_stage': 1 year ago → 3 months ago (35% weight)
    'current_stage': 3 months ago → now (25% weight)
}
```

### **⏰ Business Hours Order Patterns**
- **Peak Hours:** 9AM-5PM (weighted 4x)
- **Evening:** 5PM-9PM (weighted 2x)
- **Off-peak:** 7AM-9AM, 9PM-11PM (normal weight)

### **🎄 Seasonal Shopping Patterns**
- **December:** Christmas shopping boost
- **April-May:** Easter/Eid shopping patterns
- **30% clustering probability** during festive periods

### **👥 Customer Lifecycle Orders**
- **New customers (≤30 days):** Orders clustered in recent days
- **Medium-term (≤180 days):** Recent orders weighted higher
- **Long-term (>180 days):** Distributed throughout lifetime with seasonal patterns

## 🛠️ **Usage Instructions**

### **Fresh Database Setup**
```bash
# 1. Set up database schema
python database/setup_database.py

# 2. Generate clean, authentic data with realistic timestamps
python scripts/clean_and_regenerate_data.py

# 3. Verify results
python scripts/check_ethnic_distribution.py
```

### **Running Scripts from Root Directory**
All scripts are designed to be run from the project root:
```bash
cd customer_support_agent
python scripts/[script_name].py
python database/[script_name].py
```

## 🏆 **Benefits of New Structure**

### **For Development**
- ✅ Clear separation of concerns
- ✅ Easy navigation and maintenance
- ✅ Professional Python project layout
- ✅ Scalable architecture

### **For Data Quality**
- ✅ Realistic timestamp distributions
- ✅ Cultural authenticity maintained
- ✅ Business logic integrity
- ✅ No more "same timestamp" issues

### **For AI Hackathon**
- ✅ Production-ready codebase structure
- ✅ Professional documentation
- ✅ Easy to understand and extend
- ✅ Follows industry best practices

## 📋 **Next Steps**

1. **Run Clean Regeneration:** `python scripts/clean_and_regenerate_data.py`
2. **Verify Results:** `python scripts/check_ethnic_distribution.py`
3. **Deploy Application:** Ready for AI hackathon with authentic Nigerian data!

---
*Professional Nigerian e-commerce database with cultural authenticity and realistic business patterns*
