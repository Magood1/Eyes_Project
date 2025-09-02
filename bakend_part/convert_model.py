# convert_model.py
import tensorflow as tf

# تأكد من أن الإصدار هو 2.15 أو ما شابه
print(f"TensorFlow version: {tf.__version__}")

# المسار إلى نموذجك القديم
old_model_path = 'D:\\T5_test2\\ai_models\\expert_cataract.h5'

# المسار الذي تريد حفظ النموذج الجديد فيه
new_model_path = 'D:\\T5_test2\\ai_models\\expert_cataract.keras'

try:
    print(f"Loading model from {old_model_path}...")
    model = tf.keras.models.load_model(old_model_path)
    
    print(f"Saving model to new .keras format at {new_model_path}...")
    model.save(new_model_path)
    
    print("\nConversion successful!")
except Exception as e:
    print(f"\nAn error occurred: {e}")