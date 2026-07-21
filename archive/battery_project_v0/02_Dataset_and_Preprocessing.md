# DATASET DETAILS

---

# 3. Dataset

The dataset consists of:

| Parameter | Description |
|----------|-------------|
| Device ID | Unique Device Identifier |
| Brand | Device Manufacturer |
| Model Year | Manufacturing Year |
| Usage Type | User Behaviour |
| Daily Usage Hours | Average Usage |
| Charging Cycles | Total Charge Cycles |
| Average Charge Limit | Charging Percentage |
| Battery Health | Target Variable |
| Battery Age | Age of Battery |
| Overheating Issues | Thermal Behaviour |
| Performance Rating | Device Performance |
| Battery Type | Li-ion / Li-Po |

---

# 11. Why this Dataset?

The selected parameters directly influence battery degradation.

### Charging Cycles

More charging cycles result in:

- Capacity fade
- Increased resistance

### Daily Usage

Higher usage contributes towards:

- Faster degradation
- Thermal stress

### Battery Age

Aging causes:

- Capacity reduction
- Internal resistance growth

### Overheating

Thermal instability causes:

- Faster degradation
- Reduced battery lifespan

### Battery Type

Different battery chemistries exhibit:

- Different degradation rates
- Different charging behaviours

---

# 4. Data Preprocessing

The preprocessing pipeline includes:

- Missing value handling
- Duplicate removal
- Feature encoding
- Data normalization
- Outlier detection
- Dataset balancing

Techniques Used:

- Min-Max Scaling
- Standard Scaling
- One Hot Encoding
- Label Encoding

---

# 5. Synthetic Dataset Generation

Synthetic data generation is performed to:

- Increase dataset size
- Improve model generalization
- Preserve physical relationships

Generated Features:

- Charging Behaviour
- Thermal Behaviour
- Usage Patterns
- Battery Aging

Constraints used:

- Physical consistency
- Statistical consistency
- Realistic degradation trends
