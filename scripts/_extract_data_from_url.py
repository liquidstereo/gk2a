import re
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1])) # 현재 파일의 ".parent[1]" 경로를 root로 잡고 추가한다. 뒤의 숫자가 parent단계

from configs import Msg
from scripts._common import is_valid_image


# ========================= LEVEL1B ========================= #
l1b_urls = [
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_vi004_ea010lc_202507272220.srv.png',                        # 가시(0.47μm):파랑
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_vi005_ea010lc_202507272220.srv.png',                        # 가시(0.51μm):초록
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_vi006_ea005lc_202507272220.srv.png',                        # 가시(0.64μm):빨강
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_vi008_ea010lc_202507272220.srv.png',                        # 가시(0.86μm):식생
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_nr013_ea020lc_202507272220.srv.png',                        # 근적외(1.37μm):권운
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_nr016_ea020lc_202507272220.srv.png',                        # 근적외(1.6μm):눈/얼음
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_sw038_ea020lc_202507272220.srv.png',                        # 단파적외(3.8μm):야간안개/하층운
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_wv063_ea020lc_202507272220.srv.png',                        # 수증기(6.3μm):상층 수증기
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_wv069_ea020lc_202507272220.srv.png',                        # 수증기(6.9μm):중층 수증기
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_wv073_ea020lc_202507272220.srv.png',                        # 수증기(7.3μm):하층 수증기
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_ir087_ea020lc_202507272220.srv.png',                        # 적외(8.7μm):구름상
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_ir096_ea020lc_202507272220.srv.png',                        # 적외(9.6μm):오존
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_ir105_ea020lc_202507272220.srv.png',                        # 적외(10.5μm):깨끗한 대기창
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_ir112_ea020lc_202507272220.srv.png',                        # 적외(11.2μm):대기창
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_ir123_ea020lc_202507272220.srv.png',                        # 적외(12.3μm):오염된 대기창
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_ir133_ea020lc_202507272220.srv.png',                        # 적외(13.3μm):이산화탄소
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_rgb-true_ea010lc_202507272220.srv.png',                     # RGB 천연색
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_rgb-s-true_ea020lc_202507272220.srv.png',                   # RGB 천연색(AI):       # ← ko, ea 만 있음
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_rgb-wv1_ea020lc_202507272220.srv.png',                      # RGB 3채널 수증기
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_rgb-natural_ea020lc_202507272220.srv.png',                  # RGB 자연색
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_rgb-airmass_ea020lc_202507272220.srv.png',                  # RGB 기단
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_rgb-dust_ea020lc_202507272220.srv.png',                     # RGB 황사
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_rgb-daynight_ea020lc_202507272220.srv.png',                 # RGB 주야간 합성
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_rgb-s-daynight_ea020lc_202507272220.png',                   # RGB 주야간 합성(AI)   # ← ko, ea 만 있음
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_rgb-fog_ea020lc_202507272220.srv.png',                      # RGB 주야간 안개
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_rgb-storm_ea020lc_202507272220.srv.png',                    # RGB 주간 대류운
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_rgb-snowfog_ea020lc_202507272220.srv.png',                  # RGB 주간적설안개
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_rgb-cloud_ea020lc_202507272220.srv.png',                    # RGB 운상
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_rgb-ash_ea020lc_202507272220.srv.png',                      # RGB 화산재
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_rgb-cs_ea005lc_202507272220.srv.png',                       # RGB 구름강조          # ← ko, ea 만 있음
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_rgb-hlc_ea005lc_202507272220.srv.png',                      # RGB 상하층운          # ← ko, ea 만 있음
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_enhc-wv063_ea020lc_202507272220.srv.png',                   # 컬러수증기(6.3μm) 강조
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_enhc-wv069_ea020lc_202507272220.srv.png',                   # 컬러수증기(6.9μm) 강조
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_enhc-wv073_ea020lc_202507272220.srv.png',                   # 컬러수증기(7.3μm) 강조
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/L1B/COMPLETE/EA/202507/27/22/gk2a_ami_le1b_enhc-color-ir105_ea020lc_202507272220.srv.png'              # 컬러적외(10.5μm) 강조
]

l1b_comment = [
    '가시(0.47μm):파랑',
    '가시(0.51μm):초록',
    '가시(0.64μm):빨강',
    '가시(0.86μm):식생',
    '근적외(1.37μm):권운',
    '근적외(1.6μm):눈/얼음',
    '단파적외(3.8μm):야간안개/하층운',
    '수증기(6.3μm):상층 수증기',
    '수증기(6.9μm):중층 수증기',
    '수증기(7.3μm):하층 수증기',
    '적외(8.7μm):구름상',
    '적외(9.6μm):오존',
    '적외(10.5μm):깨끗한 대기창',
    '적외(11.2μm):대기창',
    '적외(12.3μm):오염된 대기창',
    '적외(13.3μm):이산화탄소',
    'RGB 천연색',
    'RGB 천연색(AI)',
    'RGB 3채널 수증기',
    'RGB 자연색',
    'RGB 기단',
    'RGB 황사',
    'RGB 주야간 합성',
    'RGB 주야간 합성(AI)',
    'RGB 주야간 안개',
    'RGB 주간 대류운',
    'RGB 주간적설안개',
    'RGB 운상',
    'RGB 화산재',
    'RGB 구름강조',
    'RGB 상하층운',
    '컬러수증기(6.3μm) 강조',
    '컬러수증기(6.9μm) 강조',
    '컬러수증기(7.3μm) 강조',
    '컬러적외(10.5μm) 강조'
]
# ========================= LEVEL1B ========================= #


# ========================= LEVEL2 ========================= #
l2_urls = [
    # 위험영상
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/CI/KO/202507/27/22/gk2a_ami_le2_ci-ci1_ko020lc_202507272220.srv.png',                       # 대류운발생감지:                      # ← ko
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/RR/KO/202507/27/22/gk2a_ami_le2_rr_ko020lc_202507272220.srv.png',                           # 강우강도
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/TPW/KO/202507/27/22/gk2a_ami_le2_tpw-um_ko020lc_202507272220.srv.png',                      # 가강수량(GK-2A+NWP)
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/QPN/KO/202507/27/22/gk2a_ami_le2_qpn-por_ko020lc_202507272220.srv.png',                     # 강수확률
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/QPN/KO/202507/27/22/gk2a_ami_le2_qpn-par_ko020lc_202507272220.srv.png',                     # 잠재강수량
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/AII/KO/202507/27/22/gk2a_ami_le2_aii-ki-um_ko020lc_202507272220.srv.png',                   # KI(GK-2A+NWP)                     # ← 060: area가 ea이면 020, ko 이면 060
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/AII/KO/202507/27/22/gk2a_ami_le2_aii-li-um_ko020lc_202507272220.srv.png',                   # LI(GK-2A+NWP)                     # ← 060: area가 ea이면 020, ko 이면 060
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/AII/KO/202507/27/22/gk2a_ami_le2_aii-ssi-um_ko020lc_202507272220.srv.png',                  # SSI(GK-2A+NWP)                    # ← 060: area가 ea이면 020, ko 이면 060
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/AII/KO/202507/27/22/gk2a_ami_le2_aii-tti-um_ko020lc_202507272220.srv.png',                  # TTI(GK-2A+NWP)                    # ← 060: area가 ea이면 020, ko 이면 060
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/AII/KO/202507/27/22/gk2a_ami_le2_aii-cape-um_ko020lc_202507272220.srv.png',                 # CAPE(GK-2A+NWP)
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/TQPROF/KO/202507/27/22/gk2a_ami_le2_tqprof-t300hpa-um_ko020lc_202507272220.srv.png',        # 300 hPa 온도(GK-2A+NWP)
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/TQPROF/KO/202507/27/22/gk2a_ami_le2_tqprof-t500hpa-um_ko020lc_202507272220.srv.png',        # 500 hPa 온도(GK-2A+NWP)
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/TQPROF/KO/202507/27/22/gk2a_ami_le2_tqprof-t850hpa-um_ko020lc_202507272220.srv.png',        # 850 hPa 온도(GK-2A+NWP)
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/TQPROF/KO/202507/27/22/gk2a_ami_le2_tqprof-q300hpa-um_ko020lc_202507272220.srv.png',        # 300 hPa 습도(GK-2A+NWP)
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/TQPROF/KO/202507/27/22/gk2a_ami_le2_tqprof-q500hpa-um_ko020lc_202507272220.srv.png',        # 500 hPa 습도(GK-2A+NWP)
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/TQPROF/KO/202507/27/22/gk2a_ami_le2_tqprof-q850hpa-um_ko020lc_202507272220.srv.png',        # 850 hPa 습도(GK-2A+NWP)

    # 구름
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/CTPS/KO/202507/27/22/gk2a_ami_le2_ctps-ctt_ko020lc_202507272220.srv.png',                   # 운정온도
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/CTPS/KO/202507/27/22/gk2a_ami_le2_ctps-ctp_ko020lc_202507272220.srv.png',                   # 운정기압
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/CTPS/KO/202507/27/22/gk2a_ami_le2_ctps-cth_ko020lc_202507272220.srv.png',                   # 운정고도
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/CTPS/KO/202507/27/22/gk2a_ami_le2_ctps-cp_ko020lc_202507272220.srv.png',                    # 운상
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/CLA/KO/202507/27/23/gk2a_ami_le2_cla-ct_ko020lc_202507272350.srv.png',                      # 운형
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/CLA/KO/202507/27/23/gk2a_ami_le2_cla-cll_ko020lc_202507272350.srv.png',                     # 구름 층/고도
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/CLD/KO/202507/27/23/gk2a_ami_le2_cld_ko020lc_202507272350.srv.png',                         # 구름탐지
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/DCOEW/KO/202507/27/23/gk2a_ami_le2_dcoew-cot_ko020lc_202507272350.srv.png',                 # 구름광학두께
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/DCOEW/KO/202507/27/23/gk2a_ami_le2_dcoew-cer_ko020lc_202507272350.srv.png',                 # 구름입자유효반경
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/DCOEW/KO/202507/27/23/gk2a_ami_le2_dcoew-lwp_ko020lc_202507272350.srv.png',                 # 구름수액경로
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/DCOEW/KO/202507/27/23/gk2a_ami_le2_dcoew-iwp_ko020lc_202507272350.srv.png',                 # 구름빙정경로

    # 지면/해양
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/FOG/KO/202507/27/23/gk2a_ami_le2_fog_ko020lc_202507272340.srv.png',                         # 안개
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/FF/KO/202507/27/23/gk2a_ami_le2_ff_ko020lc_202507272340.srv.png',                           # 산불탐지
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L4/FR/KO/202507/27/00/gk2a_ami_le4_fr_ko020lc_202507270000.srv.png',                           # 산불위험도                         # ← fix / LE3
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/SST/KO/202507/27/00/gk2a_ami_le2_sst_ko020lc_202507270000.srv.png',                         # 해수면온도
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L3/SST/KO/202507/27/00/gk2a_ami_le3_sst-1dm_ko020lc_202507270000.srv.png',                     # 해수면온도-1일 합성                 # ← fix / LE3
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L3/SST/KO/202507/27/00/gk2a_ami_le3_sst-5dm_ko020lc_202507270000.srv.png',                     # 해수면온도-5일 합성                 # ← fix / LE3
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L3/SST/KO/202507/27/00/gk2a_ami_le3_sst-10dm_ko020lc_202507270000.srv.png',                    # 해수면온도-10일 합성                # ← fix / LE3
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/SSC/KO/202507/27/00/gk2a_ami_le2_ssc_ko020lc_202507270000.srv.png',                         # 해류
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L4/TCHP/TP/202507/26/00/gk2a_ami_le4_tchp_tp020lc_202507260000.png',                           # 해양열용량                         # ← fix / area: tp / LE4 / ext: png <- 무조건 png
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L4/SSTA/TP/202507/25/00/gk2a_ami_le4_ssta_tp020lc_202507250000.srv.png',                       # 수온변동 지수                      # ← fix / area: tp, fd / LE4 / ext: png
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L4/OCN-OF/EA/202507/25/00/gk2a_ami_le4_ocn-of_ea020lc_202507250000.srv.png',                   # 해양 전선                         # ← fix / area: ea / LE4 / ext: png
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L4/OCN-VICING/EA/202507/25/00/gk2a_ami_le4_ocn-vicing_ea020lc_202507250000.srv.png',           # 선박 착빙                         # ← fix / area: ea / LE4 / ext: png
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/LST/EA/202507/25/00/gk2a_ami_le2_lst_ea020lc_202507250000.srv.png',                         # 지표면온도
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/SCSI/EA/202507/25/00/gk2a_ami_le2_scsi_ea020lc_202507250000.srv.png',                       # 적설/해빙
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L3/SCSI/EA/202507/25/00/gk2a_ami_le3_scsi-1dm_ea020lc_202507250000.srv.png',                   # 적설/해빙-1일 합성                     # ← fix
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/SD/EA/202507/25/00/gk2a_ami_le2_sd_ea020lc_202507250000.srv.png',                           # 적설깊이
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/VGT/EA/202507/25/00/gk2a_ami_le2_vgt-ndvi_ea020lc_202507250000.srv.png',                    # 식생지수(NDVI)                        # ← fix
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/VGT/EA/202507/25/00/gk2a_ami_le2_vgt-fvc_ea020lc_202507250000.srv.png',                     # 식생율(FVC)                       # ← fix
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/LSE/EA/202507/25/00/gk2a_ami_le2_lse-038_ea020lc_202507250000.srv.png',                     # 지표면방출률(3.8μm)               # ← fix
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/LSE/EA/202507/25/00/gk2a_ami_le2_lse-087_ea020lc_202507250000.srv.png',                     # 지표면방출률(8.7μm)               # ← fix
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/LSE/EA/202507/25/00/gk2a_ami_le2_lse-105_ea020lc_202507250000.srv.png',                     # 지표면방출률(10.5μm)              # ← fix
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/LSE/EA/202507/25/00/gk2a_ami_le2_lse-123_ea020lc_202507250000.srv.png',                     # 지표면방출률(12.3μm)              # ← fix
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/SAL/EA/202507/25/00/gk2a_ami_le2_sal-bsa_ea020lc_202507250000.srv.png',                     # 지표면반사도(Black Sky)           # ← fix
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/SAL/EA/202507/25/00/gk2a_ami_le2_sal-wsa_ea020lc_202507250000.srv.png',                     # 지표면반사도(White Sky)           # ← fix

    # 대기
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/ADPS/EA/202507/25/00/gk2a_ami_le2_adps_ea020lc_202507250000.srv.png',                       # 황사/에어로졸/화산재 탐지
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/APPS/EA/202507/25/00/gk2a_ami_le2_apps-aod_ea020lc_202507250000.srv.png',                   # 에어로졸 광학두께
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/APPS/EA/202507/25/00/gk2a_ami_le2_apps-daod055_ea020lc_202507250000.srv.png',               # 황사 광학두께
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/APPS/EA/202507/25/00/gk2a_ami_le2_apps-aep_ea020lc_202507250000.srv.png',                   # 에어로졸 입자크기
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/AVIS/EA/202507/25/00/gk2a_ami_le2_avis_ea020lc_202507250000.srv.png',                       # 에어로졸 시정
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/AMV/EA/202507/25/00/gk2a_ami_le2_amv-ir105-cd_eazzzll_202507250000.srv.png',                # 대기운동벡터(적외)                # ← resolution': 'zzzll'
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/AMV/EA/202507/25/00/gk2a_ami_le2_amv-wv063_eazzzll_202507250000.srv.png',                   # 대기운동벡터(수증기)              # ← resolution': 'zzzll'
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/AMV/EA/202507/25/00/gk2a_ami_le2_amv-sw038-cd_eazzzll_202507250000.srv.png',                # 대기운동벡터(단파복사)            # ← resolution': 'zzzll'
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/AMV/EA/202507/25/00/gk2a_ami_le2_amv-vi006-cd_eazzzll_202507250000.srv.png',                # 대기운동벡터(가시)               # ← resolution': 'zzzll'
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/TOZ/EA/202507/25/00/gk2a_ami_le2_toz_ea060lc_202507250000.srv.png',                         # 오존전량
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/SO2D/EA/202507/25/00/gk2a_ami_le2_so2d_ea020lc_202507250000.srv.png',                       # 이산화황탐지

    # 항공
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/ICING/KO/202507/25/00/gk2a_ami_le2_icing_ko020lc_202507250000.srv.png',                     # 착빙                           # ←  ko
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/OT/KO/202507/25/00/gk2a_ami_le2_ot_ko020lc_202507250000.srv.png',                           # 성층권 침투 대류운 탐지           # ←  ko
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/TFTD/KO/202507/25/00/gk2a_ami_le2_tftd_kozzzll_202507250000.srv.png',                       # 대류권계면 접힘 난류탐지           # ←  'resolution': 'zzzll'

    # 복사
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/LWRAD/KO/202507/25/00/gk2a_ami_le2_lwrad-olr_ko020lc_202507250000.srv.png',                 # 상향장파복사(대기상한)
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/LWRAD/EA/202507/27/23/gk2a_ami_le2_lwrad-dlr_ea020lc_202507272350.srv.png',                 # 하향장파복사(지표면)
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/LWRAD/EA/202507/27/23/gk2a_ami_le2_lwrad-ulr_ea020lc_202507272350.srv.png',                 # 상향장파복사(지표면)
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/SWRAD/EA/202507/27/23/gk2a_ami_le2_swrad-rsr_ea020lc_202507272350.srv.png',                 # 상향단파복사(대기상한)
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/SWRAD/EA/202507/27/23/gk2a_ami_le2_swrad-dsr_ea020lc_202507272350.srv.png',                 # 하향단파복사(표면도달일사량)
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/SWRAD/EA/202507/27/23/gk2a_ami_le2_swrad-asr_ea020lc_202507272350.srv.png',                 # 흡수단파복사(지표면)
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/AI-DSR/KO/202507/28/00/gk2a_ami_le2_ai-dsr_ko020lc_202507280000.srv.png',                   # 표면도달일사량(AI)             ← ko
    'https://nmsc.kma.go.kr/IMG/GK2A/AMI/L2/AI-UVI/KO/202507/27/23/gk2a_ami_le2_ai-uvi_ko020lc_202507272330.srv.png'                    # 자외선지수                    ← ko
]
# *** LEVEL2 *** #

l2_comment = [
    '대류운발생 탐지',
    '강우강도',
    '가강수량(GK-2A+NWP)',
    '강수확률',
    '잠재강수량',
    'KI(GK-2A+NWP)',
    'LI(GK-2A+NWP)',
    'SSI(GK-2A+NWP)',
    'TTI(GK-2A+NWP)',
    'CAPE(GK-2A+NWP)',
    '300 hPa 온도(GK-2A+NWP)',
    '500 hPa 온도(GK-2A+NWP)',
    '850 hPa 온도(GK-2A+NWP)',
    '300 hPa 습도(GK-2A+NWP)',
    '500 hPa 습도(GK-2A+NWP)',
    '850 hPa 습도(GK-2A+NWP)',
    '운정온도',
    '운정기압',
    '운정고도',
    '운상',
    '운형',
    '구름 층/고도',
    '구름탐지',
    '구름광학두께',
    '구름입자유효반경',
    '구름수액경로',
    '구름빙정경로',
    '안개',
    '산불탐지',
    '산불위험도',
    '해수면온도',
    '해수면온도-1일 합성',
    '해수면온도-5일 합성',
    '해수면온도-10일 합성',
    '해류',
    '해양열용량',
    '수온변동 지수',
    '해양 전선',
    '선박 착빙',
    '지표면온도',
    '적설/해빙',
    '적설/해빙-1일 합성',
    '적설깊이',
    '식생지수(NDVI)',
    '식생율(FVC)',
    '지표면방출률(3.8μm)',
    '지표면방출률(8.7μm)',
    '지표면방출률(10.5μm)',
    '지표면방출률(12.3μm)',
    '지표면반사도(Black Sky)',
    '지표면반사도(White Sky)',
    '황사/에어로졸/화산재 탐지',
    '에어로졸 광학두께',
    '황사 광학두께',
    '에어로졸 입자크기',
    '에어로졸 시정',
    '대기운동벡터(적외)',
    '대기운동벡터(수증기)',
    '대기운동벡터(단파복사)',
    '대기운동벡터(가시)',
    '오존전량',
    '이산화황탐지',
    '착빙',
    '성층권 침투 대류운 탐지',
    '대류권계면 접힘 난류탐지',
    '상향장파복사(대기상한)',
    '하향장파복사(지표면)',
    '상향장파복사(지표면)',
    '상향단파복사(대기상한)',
    '하향단파복사(표면도달일사량)',
    '흡수단파복사(지표면)',
    '표면도달일사량(AI)',
    '자외선지수'
]


# ========================= LEVEL2 ========================= #






def extract_level(s):
    match = re.search(r'/L(\d)(B)?/', s)
    if match:
        level_num = match.group(1)
        level = f'L{level_num}' + ('B' if match.group(2) else '')
        le_form = 'le' + level[1:].lower()
        return (level, le_form)
    return None


def extract_channel(url):
    match = re.search(r'_le[1-4]b?_([a-z0-9-]+)_[a-z]{2}[\d\w]+', url)
    return match.group(1) if match else None


def extract_category(ch):
    if ch.startswith('ai-') or ch.startswith('ocn-'):
        cat = ch
    elif '-' in ch:
        cat = ch.split('-')[0]
    else:
        cat = ch
    return cat.upper()


def extract_resolution(url):
    # 먼저 zzzll 패턴 체크
    match_zzz = re.search(r'_(?:ko|ea|tp)(zzz)ll_', url)
    if match_zzz:
        return 'zzz'

    # 그 다음 일반적인 숫자 패턴 체크 (ko, ea, tp 모두 포함)
    match_num = re.search(r'_(?:ko|ea|tp)(\d{3})lc_', url)
    if match_num:
        return match_num.group(1)

    return None


def extract_area(url):
    # zzzll 패턴에서 projection 추출
    match_zzz = re.search(r'_(ko|ea|fd)(zzz)ll_', url)
    if match_zzz:
        return match_zzz.group(1)

    # 일반적인 숫자 패턴에서 projection 추출
    match_num = re.search(r'_(ko|ea|fd|tp)(\d{3})lc_', url)
    if match_num:
        return match_num.group(1)

    return None


def extract_projection(url):
    # zzzll 패턴에서 projection 추출 (ll)
    match_zzz = re.search(r'_(?:ko|ea|fd)zzz(ll)_', url)
    if match_zzz:
        return match_zzz.group(1)

    # 일반적인 패턴에서 projection 추출 (lc)
    match_num = re.search(r'_(?:ko|ea|fd|tp)\d{3}([a-z]{2})_', url)
    if match_num:
        return match_num.group(1)
    return None


def extract_extension(url: str) -> str:
    f = os.path.basename(url)
    parts = f.split('.')
    if len(parts) > 2:
        return '.' + '.'.join(parts[-2:])
    return '.' + parts[-1]




def main():


    # gk2a_ami_le2_ai-uvi_ko020lc_202507272330.srv.png
    # 위성 센서 레벨 자료명 영역 해상도 도법 연월일시분 확장자
    # {satellite}_{sensor}_{level}_{ch}_{area}_{resolution}_{projection}_{date}.{ext}

    # 위성: gk2a
    # 센서: ami
    # 레벨: le2, l1b
    # 해상도: 020 등등...
    # 영역: fd, ea 등등...
    # 도법:




    # resolution 이 fd 일 경우 projection 는 항상 ge가 된다.
    # level 이 zzz 일 경우 projection 는 항상 ll이 된다.


    # urls = l1b_urls + l2_urls
    urls = l1b_urls
    errors = []

    year = '2025'
    month = '07'
    day = '01'
    hour = '00'
    minute = '00'




    for i, url in enumerate(urls, start=0):
        lv, f_lv = extract_level(url)
        ch = extract_channel(url)
        cat = extract_category(ch)
        resolution = extract_resolution(url)
        area = extract_area(url)
        projection = extract_projection(url)
        ext = extract_extension(url)


        # prefix = f'https://nmsc.kma.go.kr/IMG/GK2A/AMI/{lv}/{cat.upper()}/{area.upper()}/{year}{month}/{day}/{hour}/gk2a_ami_{f_lv}_'     # ← L2
        prefix = f'https://nmsc.kma.go.kr/IMG/GK2A/AMI/PRIMARY/{lv}/COMPLETE/{area.upper()}/{year}{month}/{day}/{hour}/gk2a_ami_{f_lv}_'     # ← L1B

        filename = f'{ch}_{area}{resolution}{projection}_{year}{month}{day}{hour}{minute}{ext}'
        query = f'{prefix}{filename}'
        confirm_url = is_valid_image(query, retry=False)
        m = f'{ch} / {cat} / {area} / {lv} / {f_lv} / {resolution} / {projection} / {ext} -> {confirm_url}'
        if confirm_url :
            Msg.Green(f'{l1b_comment[i]}: {m}')
        else :
            errors.append(f'{l1b_comment[i]}: {m}')
            Msg.Red(f'{l1b_comment[i]}: {m}  | {query}')




    print(f'-')

    [print(f'{i:04d} : {item}') for i, item in enumerate(errors, start=0)]




if __name__ == "__main__":
    main()