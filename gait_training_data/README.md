# Gait Training Data

This folder contains the training data used to train the local Support Vector Machine (SVM) gait classifier.

## How to add training data:

1. **Target Videos (`/target/`)**:
   - Record 5 to 10 short videos (e.g., 5-10 seconds each) of the **specific missing person** walking.
   - Record them from multiple angles if possible (e.g., walking left to right, walking towards the camera diagonally).
   - Place these `.mp4`, `.mov`, or `.avi` files here.
   - Example filename: `target_walk_1.mp4`

2. **Other People Videos (`/others/`)**:
   - Record 5 to 10 short videos of **different people** walking (friends, colleagues, etc.).
   - This teaches the model what the target person *does not* look like.
   - Place these files here.
   - Example filename: `john_walk.mp4`

After placing the videos, run the training script from the project root:

```bash
python train_gait_model.py
```
