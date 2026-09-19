작성: 2026-09-12
용도: 0908 교수님 지시 "12개 표에 연도와 계열 넣기" 결과. 노션 AgriVision 에 붙여넣기.
근거: 문서/260907_노션붙여넣기_모델선정_최종.md 4판 §6 (교수님 planning/260905_02_모델_선정.md 동결 12×12 와 대조 완료, 2026-09-12)
붙이는 법: 아래 1절(불릿)은 그냥 Ctrl+V. 2절(CSV)은 노션에서 "가져오기 → CSV" 로 올리면 표(데이터베이스)가 됨. 둘 중 편한 것 하나만.

## 12×12 grid — 헤더 12종 · 백본 12종 (연도 · 게재처 · 계열)

### 1. 헤더(디코더) 12종
- H001 FCN — 2015 CVPR — 계열: CNN 단순 업샘플 — 최소 dense prediction
- H002 U-Net-style decoder — 2015 MICCAI — 계열: 대칭 encoder-decoder — skip concatenation, BackboneUNet 으로 구현(결정 22)
- H003 Semantic FPN — 2019 CVPR (Panoptic FPN) — 계열: 피라미드 융합 — top-down pyramid fusion
- H004 PSPNet head — 2017 CVPR — 계열: pooling 문맥 — pyramid spatial pooling
- H005 DeepLabV3+ head — 2018 ECCV — 계열: atrous 문맥 — ASPP + 얕은 특징 결합
- H006 UPerNet — 2018 ECCV — 계열: PPM + FPN 복합
- H007 OCRNet — 2020 ECCV — 계열: attention 문맥 — object-region attention
- H008 AllMLPNet — 2021 NeurIPS (SegFormer 디코더) — 계열: MLP 융합 — MiT 전용이 아니라 떼어낸 AllMLPNet
- H009 FaPN — 2021 ICCV — 계열: deformable 정렬 — 계보 SFNet(ECCV 2020) → AlignSeg(TPAMI 2021) → FaPN
- H010 U-MixFormer — 2025 WACV — 계열: cross-attention 디코더 — progressive cross-attention
- H011 VWFormer — 2024 ICLR — 계열: varying-window attention — C1·파일럿0 대표 헤더(결정 26)
- H025 HamNet (LightHam) — 2021 ICLR — 계열: 행렬분해 문맥 — NMF·low-rank, attention 이 아닌 전역 문맥 대표
- 계열 합계: CNN·pooling 7, attention 3, MLP 1, 행렬분해 1
- 연도 분포: 2015 2종, 2017~2019 4종, 2020~2021 4종, 2024~2025 2종

### 2. 백본(인코더) 12종
- B001 ResNet-50 — 2016 CVPR — 계열: residual CNN — 고전 기준점(anchor)
- B002 ConvNeXt-T — 2022 CVPR — 계열: 현대 fixed-kernel CNN — 09-08 공식 IN-1K 가중치로 교체
- B004 HRNetV2-W32 — 2019 CVPR / 2020 TPAMI — 계열: 고해상도 병렬 CNN — projection 포함 30.882M
- B005 Swin-T — 2021 ICCV — 계열: window Transformer — shifted-window attention
- B006 MiT-B2 — 2021 NeurIPS (SegFormer 인코더) — 계열: 분할 전용 계층형 Transformer — C1·파일럿0 대표 백본
- B007 UniFormer-S† — 2022 ICLR (저널판 TPAMI 2023) — 계열: CNN–Transformer hybrid — 09-08 S†(head_dim 64, 23.521M)로 교체
- B008 VMamba-T — 2024 NeurIPS — 계열: visual SSM — 2D selective scan, v2 s1l8 동결(미결 13 해소)
- B016 MSCAN-B — 2022 NeurIPS (SegNeXt 인코더) — 계열: convolutional attention CNN
- B017 InternImage-T — 2023 CVPR — 계열: deformable CNN (DCNv3)
- B018 TransNeXt-Tiny — 2024 CVPR — 계열: aggregated-attention Transformer
- B019 MogaNet-S — 2024 ICLR — 계열: multi-order gated CNN — 교수님 서지·PDF 대조 09-10 완료(최종 연도·게재처는 메타데이터 동결 때 재확인)
- B020 vHeat-T — 2025 (게재처는 교수님 서지 대조 파일에만 있어 여기 미기재) — 계열: PDE/spectral heat-conduction operator — 라이선스 unspecified(결정 28)
- 계열 합계: CNN 6, Transformer 3, Hybrid 1, SSM 1, PDE/operator 1
- 연도 분포: 2016 1종, 2019 1종, 2021 2종, 2022 3종, 2023 1종, 2024 3종, 2025 1종
- 파라미터 대역: backbone-only 21~31M 사전 지정(결정 28). 실측 23.508M~30.882M

### 3. 동결 상태
- 2026-09-08 교수님이 12 백본 identity·checkpoint 전부 확정. 144조합 512×512 AMP 스모크 144/144 PASS
- 근거: platform/planning/frozen/260908_체크포인트_동결기록.md, platform/planning/260905_02_모델_선정.md §4·§8

### 4. CSV (노션 "가져오기 → CSV" 용)
```
축,ID,이름,연도,게재처,계열,한 줄 mechanism
헤더,H001,FCN,2015,CVPR,CNN 단순 업샘플,최소 dense prediction
헤더,H002,U-Net-style decoder,2015,MICCAI,대칭 encoder-decoder,skip concatenation (BackboneUNet)
헤더,H003,Semantic FPN,2019,CVPR (Panoptic FPN),피라미드 융합,top-down pyramid fusion
헤더,H004,PSPNet head,2017,CVPR,pooling 문맥,pyramid spatial pooling
헤더,H005,DeepLabV3+ head,2018,ECCV,atrous 문맥,ASPP + 얕은 특징 결합
헤더,H006,UPerNet,2018,ECCV,PPM+FPN 복합,PPM 과 FPN 결합
헤더,H007,OCRNet,2020,ECCV,attention 문맥,object-region attention
헤더,H008,AllMLPNet,2021,NeurIPS (SegFormer),MLP 융합,4단계 특징을 MLP 로만 융합
헤더,H009,FaPN,2021,ICCV,deformable 정렬,feature alignment (SFNet→AlignSeg→FaPN)
헤더,H010,U-MixFormer,2025,WACV,cross-attention 디코더,progressive cross-attention
헤더,H011,VWFormer,2024,ICLR,varying-window attention,크기가 다른 창으로 문맥
헤더,H025,HamNet (LightHam),2021,ICLR,행렬분해 문맥,NMF low-rank 전역 문맥
백본,B001,ResNet-50,2016,CVPR,residual CNN,residual bottleneck (anchor)
백본,B002,ConvNeXt-T,2022,CVPR,현대 fixed-kernel CNN,modernized large-kernel CNN
백본,B004,HRNetV2-W32,2019,CVPR / TPAMI 2020,고해상도 병렬 CNN,고해상도 유지 병렬 branch
백본,B005,Swin-T,2021,ICCV,window Transformer,shifted-window attention
백본,B006,MiT-B2,2021,NeurIPS (SegFormer),분할 전용 계층형 Transformer,overlapping patch + SR attention
백본,B007,UniFormer-S†,2022,ICLR (TPAMI 2023),CNN–Transformer hybrid,얕은 층 conv + 깊은 층 attention
백본,B008,VMamba-T,2024,NeurIPS,visual SSM,2D selective scan (v2 s1l8)
백본,B016,MSCAN-B,2022,NeurIPS (SegNeXt),convolutional attention CNN,multi-scale depthwise conv attention
백본,B017,InternImage-T,2023,CVPR,deformable CNN,DCNv3
백본,B018,TransNeXt-Tiny,2024,CVPR,aggregated-attention Transformer,aggregated attention
백본,B019,MogaNet-S,2024,ICLR,multi-order gated CNN,multi-order gated aggregation
백본,B020,vHeat-T,2025,미기재(교수님 서지 대조 완료),PDE/spectral operator,heat-conduction operator
```
