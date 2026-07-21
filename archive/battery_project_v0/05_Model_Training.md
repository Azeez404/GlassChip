# MODEL TRAINING

---

# 16. Total PINN Loss

The Total Loss consists of:

Total Loss =

- Data Loss
- Physics Loss
- Boundary Loss (if applicable)

Mathematically,

Ltotal=

Ldata + λLphysics

where,

- λ = Physics weight parameter

---

# 17. Optimizer Used

Possible optimizers include:

- Adam
- AdamW
- L-BFGS

Recommended Pipeline:

Adam

↓

AdamW

↓

L-BFGS Fine Tuning

---

# 12. Optimization Techniques

Techniques Used:

- Automatic Differentiation
- Learning Rate Scheduling
- Physics Residual Minimization
- Gradient Based Optimization

---

# Activation Functions

Recommended:

- Tanh
- GELU
- SiLU
- ReLU

Preferred:

- Tanh
- GELU

Reason:

They perform better for smooth function approximations.
