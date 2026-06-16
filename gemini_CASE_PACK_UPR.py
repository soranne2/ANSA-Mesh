import ansa
from ansa import base, mesh, constants

def process_case_pack_upr():
    target_prop_name = "CASE_PACK_UPR"
    
    # 1. Target Property 찾기
    props = base.CollectEntities(constants.NASTRAN, None, "PSHELL") 
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
    midsurf_faces = base.FacesMiddle(faces)
    
    # 🔥 에러가 발생했던 중복 else 문을 하나로 통합한 부분입니다.
    if not midsurf_faces:
        print("Warning: Mid-surface 추출에 실패했거나 추가적인 수동 형상 정리가 필요할 수 있습니다. 원본 Face에 메쉬를 진행합니다.")
        faces_to_mesh = faces
    else:
        print("Mid-surface 추출 완료.")
        faces_to_mesh = midsurf_faces

    # 3. Mesh Parameters (Target=5, Min=2, Max=5) 설정
    print("Mesh 파라미터를 설정합니다...")
    mesh.SetMacroResolution(length=5.0)
    
    mesh_params = mesh.MeshParam()
    mesh_params.target_length = 5.0
    mesh_params.min_length = 2.0
    mesh_params.max_length = 5.0
    
    # 4. Hole Treatment 및 Washer 설정 (8 Nodes, 2-Layer Washer)
    print("Hole 및 Washer (8 nodes, 2 layers) 설정을 적용합니다...")
    
    holes = base.CollectEntities(constants.NASTRAN, faces_to_mesh, "HOLE")
    
    for hole in holes:
        # Hole 주변 노드 개수를 8개로 강제 할당
        mesh.SetNum(hole, 8)
        
        # Washer 생성: offset_distance=1.0, layers=2 (1, 1 간격)
        try:
            mesh.CreateWasher(hole, offset_distance=1.0, elements_number=2)
        except Exception as e:
            print(f"Warning: 특정 Hole에 Washer 적용 실패 - {e}")

    # 5. Mesh 생성 (Free Mesh)
    print("Meshing을 시작합니다...")
    mesh.MeshFree(faces_to_mesh, mesh_params)
    
    print("모든 작업이 완료되었습니다!")

# 스크립트 실행
if __name__ == '__main__':
    process_case_pack_upr()
