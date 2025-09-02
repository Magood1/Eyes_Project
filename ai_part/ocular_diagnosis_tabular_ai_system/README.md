# FILE: README.md

# نظام تشخيص أمراض العيون - النموذج الجدولي (الإصدار 2.0)

هذا المشروع هو إطار عمل مستقل ومُحصَّن لتدريب وتقييم نموذج جدولي (Meta-model) يعتمد على مخرجات نماذج تصنيف صور قاع العين لتقديم تشخيص نهائي.

## الميزات الرئيسية (الإصدار 2.0)

- **الاستقلالية الكاملة (Decoupled):** يعمل كنظام منفصل تمامًا، ويتفاعل مع النماذج الصورية المحفوظة عبر "محول" (Adapter)، مما يمنع تداخل الاعتماديات.
- **قابلية التوسع المعمارية:** يستخدم نمط تصميم الاستراتيجية (`FusionStrategy`)، مما يسمح بتبديل طرق دمج الميزات بسهولة عبر ملف التكوين.
- **الأمان والخصوصية:** يقوم بإخفاء هوية المرضى تلقائيًا عن طريق استبدال المعرفات الحقيقية بـ `UUIDs` أثناء توليد الميزات.
- **الموثوقية وقابلية إعادة الإنتاج:** يضمن استقرار تقسيم البيانات باستخدام `seed` مخصص، ويدعم تنسيق `Parquet` عالي الأداء.
- **أساس للاختبار:** يتضمن اختبارات وحدة (Unit Tests) للتحقق من صحة منطق دمج الميزات.

## سير العمل (Workflow)

المشروع مقسم إلى مساري عمل واضحين:

### 1. توليد الميزات (Feature Generation)

هذه الخطوة يتم تشغيلها مرة واحدة لإعداد مجموعة البيانات الجدولية.

```bash
# قم بتعديل configs/1_feature_generation_config.yaml لتحديد مسارات النماذج الصورية
python generate_features.py --config configs/1_feature_generation_config.yaml


# قم بتعديل configs/2_tabular_training_config.yaml لتحديد معلمات النموذج
python train_tabular.py --config configs/2_tabular_training_config.yaml

#تقييم النموذج الجدولي
python evaluate_tabular.py --config configs/2_tabular_training_config.yaml --weights path/to/model_weights.h5

#إعداد البيئة
pip install -r requirements.txt