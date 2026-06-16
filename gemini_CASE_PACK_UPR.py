import ansa
from ansa import base, mesh, constants

def process_case_pack_upr():
    target_prop_name = "CASE_PACK_UPR"
    
    # 1. Target Property 찾기
    props = base.CollectEntities(constants.NASTRAN, None, "PSHELL") # Deck 환경에 따라 변경 가능 (예: "PROPATY" for Abaqus)
    target_prop = None
    for p in props:
        if p._name == target_prop_name:
            target_prop = p
            break
            
    if not target_prop:
        print(f"Error: '{target_prop_name}' 프로퍼티를 찾을 수 없습니다.")
        return

    # 해당 프로퍼티를 가진 파트/페이스 수집
    faces = base.CollectEntities(constants.NASTRAN, target_prop, "FACE")
    if not faces:
        print("Error: 선택된 프로퍼티에 할당된 Face가 없습니다.")
        return

    print(f"'{target_prop_name}' 프로퍼티 인식 완료. Mid-surface 작업을 시작합니다.")

    # 2. Mid-surface 생성
    # 형상에 따라 base.FacesMiddle 또는 Skin/Cast 기능 등을 사용해야 할 수 있습니다.
    # 아래는 가장 기본적인 면 사이의 중간면을 생성하는 API 예시입니다.
    midsurf_faces = base.FacesMiddle(faces)
    if not midsurf_faces:
        print("Warning: Mid-surface 추출에 실패했거나 추가적인 수동 형상 정리가 필요할 수 있습니다.")
    else:
        print("Mid-surface 추출 완료.")
        faces_to_mesh = midsurf_faces
    else:
        # Mid-surface 실패 시 원본에 메쉬를 진행하도록 fallback
        faces_to_mesh = faces

    # 3. Mesh Parameters (Target=5, Min=2, Max=5) 설정
    print("Mesh 파라미터를 설정합니다...")
    mesh.SetMacroResolution(length=5.0)
    
    # 세부 메쉬 퀄리티 및 사이즈 파라미터 셋팅 (Feature lines, perimeters 등)
    mesh_params = mesh.MeshParam()
    mesh_params.target_length = 5.0
    mesh_params.min_length = 2.0
    mesh_params.max_length = 5.0
    
    # 4. Hole Treatment 및 Washer 설정 (8 Nodes, 2-Layer Washer)
    # ANSA Feature Manager를 통한 접근이나 직접 Perimeter node 설정
    print("Hole 및 Washer (8 nodes, 2 layers) 설정을 적용합니다...")
    
    # 모델 내의 모든 Hole을 찾습니다.
    holes = base.CollectEntities(constants.NASTRAN, faces_to_mesh, "HOLE")
    
    for hole in holes:
        # Hole 주변 노드 개수를 8개로 강제 할당
        mesh.SetNum(hole, 8)
        
        # Washer 생성: offset_distance=1.0, layers=2 (1, 1 간격)
        # ANSA 버전에 따라 CreateWasher의 파라미터가 다를 수 있으나 일반적인 형태입니다.
        try:
            mesh.CreateWasher(hole, offset_distance=1.0, elements_number=2)
        except Exception as e:
            print(f"Warning: 특정 Hole에 Washer 적용 실패 - {e}")

    # 5. Mesh 생성 (Free Mesh 또는 Batch Mesh)
    print("Meshing을 시작합니다...")
    # 추출된 Mid-surface 또는 대상 Face에 대해 메쉬 수행
    mesh.MeshFree(faces_to_mesh, mesh_params)
    
    print("모든 작업이 완료되었습니다!")

# 스크립트 실행
if __name__ == '__main__':
    process_case_pack_upr()
