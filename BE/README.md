# Test Questions and SQL Queries for School Database

## STUDENT Table

1. นักเรียนที่มาจากจังหวัดเชียงใหม่มีกี่คนและแบ่งตามระดับชั้นเรียนอย่างไร
   ```sql
   SELECT ชั้น, COUNT(*) as จำนวนนักเรียน FROM STUDENT WHERE จังหวัด = 'จ.เชียงใหม่' GROUP BY ชั้น ORDER BY ชั้น;
   ```

2. นักเรียนในแต่ละอำเภอของจังหวัดเชียงใหม่มีจำนวนเท่าไหร่
   ```sql
   SELECT อำเภอ, COUNT(*) as จำนวนนักเรียน FROM STUDENT WHERE จังหวัด = 'จ.เชียงใหม่' GROUP BY อำเภอ ORDER BY จำนวนนักเรียน DESC;
   ```

3. นักเรียนที่อยู่อำเภอเมืองเชียงใหม่มีพ่อทำอาชีพอะไรบ้าง
   ```sql
   SELECT อาชีพของบิดา, COUNT(*) as จำนวน FROM STUDENT WHERE จังหวัด = 'จ.เชียงใหม่' AND อำเภอ = 'อ.เมืองเชียงใหม่' GROUP BY อาชีพของบิดา ORDER BY จำนวน DESC;
   ```

4. สัดส่วนสถานะภาพครอบครัวของนักเรียนทั้งหมดเป็นเปอร์เซ็นต์เท่าไหร่
   ```sql
   SELECT [สถานะภาพครอบครัว] AS family_status, ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM STUDENT), 2) AS percentage FROM STUDENT GROUP BY [สถานะภาพครอบครัว];
   ```

5. นักเรียนที่มีพ่อทำอาชีพเกี่ยวกับราชการและอยู่กรุงเทพมีใครบ้างและอยู่ชั้นไหน
   ```sql
   SELECT รหัสประจำตัว,อาชีพของบิดา,จังหวัด, ชื่อ || ' ' || นามสกุล AS full_name, ชั้น 
   FROM STUDENT 
   WHERE อาชีพของบิดา LIKE '%ราชการ%' AND จังหวัด LIKE 'จ.กรุงเทพ%';


   

## SCORING Table

1. นักเรียนที่มีคะแนนต่ำกว่า 50 เปอร์เซ็นต์ในวิชาไหนมีจำนวนมากที่สุด
   ```sql
   SELECT ชื่อวิชา, COUNT(*) as จำนวนนักเรียนที่คะแนนต่ำ
   FROM SCORING 
   WHERE ร้อยละ < 50
   GROUP BY ชื่อวิชา
   ORDER BY จำนวนนักเรียนที่คะแนนต่ำ DESC
   LIMIT 5;
   ```

2. นักเรียนคนไหนมีคะแนนเฉลี่ยต่ำที่สุดในปีการศึกษา 2567
   ```sql
   SELECT รหัสประจำตัวนักเรียน, 
          AVG(ร้อยละ) as คะแนนเฉลี่ย,
          COUNT(*) as จำนวนวิชา
   FROM SCORING 
   WHERE ปีการศึกษา = 2567
   GROUP BY รหัสประจำตัวนักเรียน
   ORDER BY คะแนนเฉลี่ย ASC
   LIMIT 10;
   ```

3. วิชาที่นักเรียนได้เกรด F มากที่สุดคือวิชาอะไร
   ```sql
   SELECT ชื่อวิชา, ชื่อวิชาภาษาอังกฤษ, COUNT(*) as จำนวนเกรดF
   FROM SCORING 
   WHERE เกรด = 'F'
   GROUP BY ชื่อวิชา, ชื่อวิชาภาษาอังกฤษ
   ORDER BY จำนวนเกรดF DESC;
   ```

4. นักเรียนที่ได้คะแนนต่ำกว่า 60 เปอร์เซ็นต์ในมากกว่า 3 วิชามีกี่คน
   ```sql
   SELECT COUNT(*) as จำนวนนักเรียน
   FROM (
       SELECT รหัสประจำตัวนักเรียน, COUNT(*) as จำนวนวิชาที่คะแนนต่ำ
       FROM SCORING 
       WHERE ร้อยละ < 60
       GROUP BY รหัสประจำตัวนักเรียน
       HAVING COUNT(*) > 3
   );
   ```

5. วิชาไหนมีคะแนนเฉลี่ยสูงที่สุดและต่ำที่สุด
   ```sql
   SELECT ชื่อวิชา, 
          ROUND(AVG(ร้อยละ), 2) as คะแนนเฉลี่ย,
          COUNT(*) as จำนวนนักเรียน
   FROM SCORING 
   GROUP BY ชื่อวิชา
   ORDER BY คะแนนเฉลี่ย DESC;
   ```

## ATTENDANCE Table

1. นักเรียนที่ขาดเรียนมากกว่า 10 วันในปีการศึกษา 2020 มีกี่คน
   ```sql
   SELECT COUNT(DISTINCT รหัสนักเรียน) as จำนวนนักเรียน
   FROM ATTENDANCE 
   WHERE ปีการศึกษา = 2567 AND ประเภท = 'ขาด'
   GROUP BY รหัสนักเรียน
   HAVING COUNT(*) > 10;
   ```

<!-- 2. นักเรียนคนไหนขาดเรียนมากที่สุดในภาคเรียนที่ 1 ปีการศึกษา 2019
   ```sql
   SELECT รหัสนักเรียน, COUNT(*) as จำนวนวันที่ขาด
   FROM ATTENDANCE 
   WHERE ปีการศึกษา = 2567 AND ภาคเรียน = 1 AND ประเภท = 'ขาด'
   GROUP BY รหัสนักเรียน
   ORDER BY จำนวนวันที่ขาด DESC
   LIMIT 10;
   ``` -->

3. สถิติการมาสายของนักเรียนในแต่ละเดือนของปีการศึกษา 2021
   ```sql
   SELECT strftime('%m', วันที่) as เดือน, COUNT(*) as จำนวนครั้งที่มาสาย
   FROM ATTENDANCE 
   WHERE ปีการศึกษา = 2567 AND ประเภท = 'มาสาย'
   GROUP BY strftime('%m', วันที่)
   ORDER BY เดือน;
   ```

4. เปอร์เซ็นต์การขาดเรียน ลาป่วย และมาสายของนักเรียนทั้งหมด
   ```sql
   SELECT ประเภท, 
          COUNT(*) as จำนวน,
          ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ATTENDANCE), 2) as เปอร์เซ็นต์
   FROM ATTENDANCE 
   GROUP BY ประเภท
   ORDER BY จำนวน DESC;
   ```

5. นักเรียนที่ไม่เคยขาดเรียนในปีการศึกษา 2024 มีกี่คน
   ```sql
   SELECT COUNT(DISTINCT s.รหัสประจำตัว) as นักเรียนที่ไม่เคยขาด
   FROM STUDENT s
   WHERE s.รหัสประจำตัว NOT IN (
       SELECT DISTINCT รหัสนักเรียน 
       FROM ATTENDANCE 
       WHERE ปีการศึกษา = 2567 AND ประเภท = 'ขาด'
   );
   ```

## LIBRARY Table

1. นักเรียนคนไหนเข้าห้องสมุดบ่อยที่สุดในปี 2567
   ```sql
   SELECT รหัสประจำตัวนักเรียน, COUNT(*) as จำนวนครั้ง
   FROM LIBRARY 
   WHERE strftime('%Y', วันเวลาที่เข้าห้องสมุด) = '2567'
   GROUP BY รหัสประจำตัวนักเรียน
   ORDER BY จำนวนครั้ง DESC
   LIMIT 10;
   ```

2. แต่ละระดับชั้นมีนักเรียนเข้าห้องสมุดเฉลี่ยกี่คนต่อเดือน
   ```sql
   SELECT s.ชั้น, 
          strftime('%Y-%m', l.วันเวลาที่เข้าห้องสมุด) as เดือน,
          COUNT(DISTINCT l.รหัสประจำตัวนักเรียน) as จำนวนนักเรียน
   FROM LIBRARY l
   JOIN STUDENT s ON l.รหัสประจำตัวนักเรียน = s.รหัสประจำตัว
   GROUP BY s.ชั้น, strftime('%Y-%m', l.วันเวลาที่เข้าห้องสมุด)
   ORDER BY s.ชั้น, เดือน;
   ```

3. ห้องสมุดมีผู้ใช้บริการมากที่สุดในช่วงเวลาไหนของวัน
   ```sql
   SELECT CASE 
              WHEN strftime('%H', วันเวลาที่เข้าห้องสมุด) BETWEEN '06' AND '11' THEN 'เช้า'
              WHEN strftime('%H', วันเวลาที่เข้าห้องสมุด) BETWEEN '12' AND '17' THEN 'บ่าย'
              ELSE 'เย็น'
          END as ช่วงเวลา,
          COUNT(*) as จำนวนครั้ง
   FROM LIBRARY 
   GROUP BY ช่วงเวลา
   ORDER BY จำนวนครั้ง DESC;
   ```

4. เดือนไหนมีการใช้บริการห้องสมุดมากที่สุด
   ```sql
   SELECT strftime('%m', วันเวลาที่เข้าห้องสมุด) as เดือน,
          COUNT(*) as จำนวนครั้ง,
          COUNT(DISTINCT รหัสประจำตัวนักเรียน) as จำนวนนักเรียน
   FROM LIBRARY 
   GROUP BY strftime('%m', วันเวลาที่เข้าห้องสมุด)
   ORDER BY จำนวนครั้ง DESC;
   ```

5. นักเรียนที่ไม่เคยเข้าห้องสมุดเลยมีกี่คนแบ่งตามชั้นเรียน
   ```sql
   SELECT s.ชั้น, COUNT(*) as จำนวนนักเรียนที่ไม่เข้าห้องสมุด
   FROM STUDENT s
   LEFT JOIN LIBRARY l ON s.รหัสประจำตัว = l.รหัสประจำตัวนักเรียน
   WHERE l.รหัสประจำตัวนักเรียน IS NULL
   GROUP BY s.ชั้น
   ORDER BY s.ชั้น;
   ```

## FOOD Table

1. นักเรียนชอบซื้ออาหารหรือขนมประเภทไหนมากที่สุด3อันดับในโรงอาหาร
   ```sql
   SELECT product_categories, SUM(amount) AS total_amount FROM FOOD WHERE source = 'canteen' AND student_id IS NOT NULL GROUP BY product_categories ORDER BY total_amount DESC LIMIT 3;
   ```

2. 
นักเรียนซื้ออาหารมากแค่ไหนเทียบกับขนม
   ```sql
   SELECT SUM(CASE WHEN product_categories = 'อาหาร' THEN total_price ELSE 0 END) AS total_food, SUM(CASE WHEN product_categories = 'ขนม' THEN total_price ELSE 0 END) AS total_snack, SUM(CASE WHEN product_categories = 'อาหาร' THEN total_price ELSE 0 END) / NULLIF(SUM(CASE WHEN product_categories = 'ขนม' THEN total_price ELSE 0 END), 0) AS food_to_snack_ratio FROM FOOD WHERE product_categories IN ('อาหาร', 'ขนม');
   ```

3. นักเรียนซื้ออาหารจากที่ไหนมากที่สุด
   ```sql
   SELECT source, SUM(total_price) AS total_spent FROM FOOD GROUP BY source ORDER BY total_spent DESC LIMIT 1;
   ```

4. นักเรียนซื้ออาหารจากที่ไหนเท่าไหร่บ้างในปี2025
   ```sql
   SELECT source AS แหล่งซื้ออาหาร, SUM(total_price) AS ยอดรวม, SUM(amount) AS จำนวนรวม FROM FOOD WHERE strftime('%Y', transaction_date) = '2025' GROUP BY source;
   ```

5. การซื้ออุปกรณ์เครื่องเขียนในแต่ละเดือนมีแนวโน้มเพิ่มขึ้นหรือลดลง
   ```sql
   SELECT strftime('%Y-%m', transaction_date) AS month, SUM(amount) AS total_quantity, SUM(total_price) AS total_spent FROM FOOD WHERE product_categories = 'อุปกรณ์เครื่องเขียน' GROUP BY month ORDER BY month;
   ```

## HOSPITAL Table

1. นักเรียนที่มาใช้บริการห้องพยาบาลด้วยอาการแผลมีกี่เปอร์เซ็นต์ของการมาใช้บริการทั้งหมด
   ```sql
   SELECT 
       COUNT(*) FILTER (WHERE อาการหรือสาเหตุ LIKE '%แผล%') * 100.0 / COUNT(*) as เปอร์เซ็นต์แผล
   FROM HOSPITAL;
   ```

2. นักเรียนมีอาการปวดท้องมากี่เปอร์เซ็นต์ของการมาใช้บริการทั้งหมด
   ```sql
   SELECT 
       COUNT(*) FILTER (WHERE อาการหรือสาเหตุ LIKE '%ปวดท้อง%' OR อาการหรือสาเหตุ LIKE '%ท้องเสิย%') * 100.0 / COUNT(*) as เปอร์เซ็นต์ปวดท้อง
   FROM HOSPITAL;
   ```

<!-- 3. มีนักเรียนเข้าห้องพยาบาลเพราะได้รับบาดเจ็บจากสถานที่ไหนมากที่สุด
   ```sql
   SELECT location, COUNT(*) AS cnt FROM ( SELECT CASE WHEN [รายละเอียด] LIKE '%อัฒจันทร์วงกลม%' THEN 'อัฒจันทร์วงกลม' WHEN [รายละเอียด] LIKE '%ตึกมงฟอร์ต%' THEN 'ตึกมงฟอร์ต' WHEN [รายละเอียด] LIKE '%สนามฟุตบอล%' THEN 'สนามฟุตบอล' WHEN [รายละเอียด] LIKE '%ห้องเรียน%' THEN 'ห้องเรียน' WHEN [รายละเอียด] LIKE '%โรงอาหาร%' THEN 'โรงอาหาร' WHEN [รายละเอียด] LIKE '%ห้องสมุด%' THEN 'ห้องสมุด' WHEN [รายละเอียด] LIKE '%มินิมาร์ท%' THEN 'มินิมาร์ท' WHEN [รายละเอียด] LIKE '%สระว่ายน้ำ%' THEN 'สระว่ายน้ำ' WHEN [รายละเอียด] LIKE '%ลานจอดรถ%' THEN 'ลานจอดรถ' WHEN [รายละเอียด] LIKE '%ตึกสามัคคีนฤมิต%' THEN 'ตึกสามัคคีนฤมิต' WHEN [รายละเอียด] LIKE '%ลานอเนกประสงค์กรีนโดม%' THEN 'ลานอเนกประสงค์กรีนโดม' WHEN [รายละเอียด] LIKE '%อาคารเซนต์คาเบรียล%' THEN 'อาคารเซนต์คาเบรียล' ELSE NULL END AS location FROM HOSPITAL WHERE [รายละเอียด] IS NOT NULL ) WHERE location IS NOT NULL GROUP BY location ORDER BY cnt DESC LIMIT 1;
   ``` -->

4. เดือนไหนมีการใช้บริการห้องพยาบาลมากที่สุด
   ```sql
   SELECT strftime('%m', วันที่) as เดือน, 
          COUNT(*) as จำนวนครั้ง
   FROM HOSPITAL 
   WHERE วันที่ IS NOT NULL
   GROUP BY strftime('%m', วันที่)
   ORDER BY จำนวนครั้ง DESC;
   ```

5. นักเรียนคนไหนมาใช้บริการห้องพยาบาลบ่อยที่สุดและมีอาการอะไรบ้าง
   ```sql
   SELECT รหัสประจำตัวนักเรียน, 
          COUNT(*) as จำนวนครั้ง,
          GROUP_CONCAT(DISTINCT อาการหรือสาเหตุ) as อาการต่างๆ
   FROM HOSPITAL 
   WHERE รหัสประจำตัวนักเรียน IS NOT NULL
   GROUP BY รหัสประจำตัวนักเรียน
   ORDER BY จำนวนครั้ง DESC
   LIMIT 10;
   ```
