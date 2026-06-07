import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ph_music.verify import analyze_song, intervals
# Paper Table 1, J-Sangnyeongsan geomungo:
#   d1: C1[1/11,1/8], C2[1/5,1/4]   d3: C1[1/11,1/8]   d2: C1[1/11,1/8]
res = analyze_song("01 J-Sangnyeongsan_Geomungo_part(0719)")
for k in ("d1", "d3", "d2"):
    print(k, [(round(b,4), round(d,4)) for b, d in intervals(res, k)])
print("Expect d1 has 2 bars incl ~[0.0909,0.125] and ~[0.2,0.25]; d2/d3 have the [0.0909,0.125] bar.")
