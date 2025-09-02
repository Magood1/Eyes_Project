# FILE: ocular_diagnosis_system/ai_pipeline/production_feature_pipeline.py

import pandas as pd
import numpy as np
import logging

class ProductionFeaturePipeline:
    """
    خط أنابيب مُحسَّن للإنتاج (Hotfix v2.0).
    يقوم بتحويل متجه الميزات الأولي (18 ميزة) إلى المتجه النهائي (38 ميزة)
    الذي يتوقعه النموذج، مع ضمان تطابق 100% مع مسار التدريب.
    """
    def __init__(self):
        # --- 1. تعريف الأعمدة بالترتيب الدقيق كما في سجل التدريب ---
        self.initial_feature_names = [
            'Age', 'Sex',
            'Left_normal', 'Left_cataract', 'Left_diabetic', 'Left_glaucoma', 'Left_hyper', 'Left_Myopia', 'left_AMD', 'Left_other',
            'Right_normal', 'Right_cataract', 'Right_diabetic', 'Right_glaucoma', 'Right_hyper', 'Right_Myopia', 'Right_AMD', 'Right_other'
        ]
        
        # الترتيب الدقيق للميزات الرقمية الـ 32 كما تم تمريرها إلى StandardScaler
        self.numerical_feature_order_from_training = [
            'Age', 'Left_normal', 'Left_cataract', 'Left_diabetic', 'Left_glaucoma', 'Left_hyper', 'Left_Myopia', 'left_AMD', 'Left_other',
            'Right_normal', 'Right_cataract', 'Right_diabetic', 'Right_glaucoma', 'Right_hyper', 'Right_Myopia', 'Right_AMD', 'Right_other',
            'Max_Myopia', 'Avg_Myopia', 'Max_cataract', 'Avg_cataract', 'Max_diabetic', 'Avg_diabetic',
            'Max_glaucoma', 'Avg_glaucoma', 'Max_hyper', 'Avg_hyper', 'Max_normal', 'Avg_normal',
            'Max_other', 'Avg_other', 'Overall_Max_Score_Sum'
        ]

        # الترتيب الدقيق للميزات التصنيفية الـ 2 كما تم تمريرها إلى OneHotEncoder
        self.categorical_feature_order_from_training = ['Sex', 'Age_Group']

        # --- 2. تضمين الحالات (States) الحقيقية من التدريب ---
        self.scaler_means = np.array([
            6.06505526e+01, 2.65586310e-01, 6.17511755e-01, 2.01106543e-02, 5.83307688e-02, 1.32981920e-02, 1.00074925e-02, 3.90120088e-03, 1.12536332e-02,
            2.67404215e-01, 6.18107178e-01, 1.99470577e-02, 5.66402959e-02, 1.32046842e-02, 9.75564096e-03, 3.84709038e-03, 1.10938417e-02,
            1.01789867e-02, 9.88156673e-03, 6.26264992e-01, 6.17809466e-01, 2.05675531e-02, 2.00288560e-02, 5.90940314e-02, 5.74855323e-02,
            1.37672667e-02, 1.32514381e-02, 2.75035682e-01, 2.66495263e-01, 1.15264224e-02, 1.11737374e-02, 1.01643493e+00
        ])
        
        self.scaler_scales = np.array([
            1.25299908e+01, 3.75444638e-02, 4.07158950e-02, 2.22181724e-03, 5.47433738e-03, 2.21125594e-03, 1.02301962e-03, 4.80491438e-04, 1.26571886e-03,
            3.32055017e-02, 3.86323169e-02, 1.92129394e-03, 4.80496955e-03, 1.84600343e-03, 8.54981016e-04, 4.33185615e-04, 1.18258010e-03,
            8.38087396e-04, 8.53665652e-04, 3.72389260e-02, 3.75160528e-02, 1.88051032e-03, 1.92714541e-03, 4.91096583e-03, 4.74997897e-03,
            1.73269802e-03, 1.89161235e-03, 3.82391976e-02, 3.30287820e-02, 1.05972564e-03, 1.10982855e-03, 2.04195541e-02
        ])
        
        self.onehot_categories = [
            np.array([0, 1]),  # 'Sex'
            np.array(['0-40', '41-60', '61-80', '80+']) # 'Age_Group'
        ]

    def _feature_engineer(self, df: pd.DataFrame) -> pd.DataFrame:
        """تطبيق هندسة الميزات لتوسيع البيانات من 18 إلى 34 ميزة."""
        df_eng = df.copy()
        
        # Age Binning
        age_bins = [0, 40, 60, 80, np.inf]
        age_labels = ['0-40', '41-60', '61-80', '80+']
        df_eng['Age_Group'] = pd.cut(df_eng['Age'], bins=age_bins, labels=age_labels, right=False)
        
        # Aggregated Scores
        conditions = ['Myopia', 'cataract', 'diabetic', 'glaucoma', 'hyper', 'normal', 'other']
        # ملاحظة: 'AMD' غير موجودة في سجل التدريب لـ Aggregated Scores
        
        for cond in conditions:
            # مطابقة أسماء الأعمدة بحساسية لحالة الأحرف
            left_col = next((c for c in df.columns if c.lower() == f'left_{cond}'.lower()), None)
            right_col = next((c for c in df.columns if c.lower() == f'right_{cond}'.lower()), None)
            
            if left_col and right_col:
                df_eng[f'Max_{cond}'] = df_eng[[left_col, right_col]].max(axis=1)
                df_eng[f'Avg_{cond}'] = df_eng[[left_col, right_col]].mean(axis=1)

        # Overall Disease Load
        max_score_cols = [c for c in df_eng.columns if c.startswith('Max_')]
        if max_score_cols:
            df_eng['Overall_Max_Score_Sum'] = df_eng[max_score_cols].sum(axis=1)
            
        return df_eng

    def transform(self, input_vector: np.ndarray) -> np.ndarray:
        """
        الدالة الرئيسية التي تأخذ متجهًا من 18 ميزة وتحوله إلى 38 ميزة.
        """
        if input_vector.shape != (18,):
            raise ValueError(f"المتجه المدخل يجب أن يكون بطول 18, ولكن تم استقبال شكل {input_vector.shape}")
        
        # 1. تحويل المتجه إلى DataFrame
        input_df = pd.DataFrame([input_vector], columns=self.initial_feature_names)
        
        # 2. تطبيق هندسة الميزات
        engineered_df = self._feature_engineer(input_df)
        
        # 3. تطبيق المعالجة المسبقة (Scaling + OneHotEncoding)
        
        # --- التحجيم (Scaling) ---
        numerical_data = engineered_df[self.numerical_feature_order_from_training].values
        scaled_numerical = (numerical_data - self.scaler_means) / self.scaler_scales
        
        # --- التشفير (One-Hot Encoding) ---
        categorical_data = engineered_df[self.categorical_feature_order_from_training]
        
        # Sex
        sex_col = categorical_data['Sex'].values.reshape(-1, 1)
        sex_onehot = (sex_col == self.onehot_categories[0]).astype(float)

        # Age_Group
        age_group_col = categorical_data['Age_Group'].values
        age_group_onehot = np.zeros((len(age_group_col), len(self.onehot_categories[1])))
        for i, val in enumerate(age_group_col):
            cat_idx = np.where(self.onehot_categories[1] == val)[0]
            if len(cat_idx) > 0:
                age_group_onehot[i, cat_idx[0]] = 1.0

        # --- 4. دمج كل شيء بالترتيب الصحيح ---
        final_vector = np.concatenate([scaled_numerical, sex_onehot, age_group_onehot], axis=1)
        
        if final_vector.shape[1] != 38:
            logging.error(f"خطأ في الأبعاد! الشكل النهائي هو {final_vector.shape}, ولكن المتوقع هو (1, 38).")
            raise RuntimeError("فشل خط أنابيب الميزات في إنتاج الشكل الصحيح.")
            
        return final_vector