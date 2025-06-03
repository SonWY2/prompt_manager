  // 그룹 삭제 기능
  const deleteGroup = useCallback(async (groupName) => {
    try {
      // 해당 그룹에 속한 태스크 확인 및 업데이트
      setTasks(prevTasks => {
        const tasksInGroup = Object.entries(prevTasks).filter(([_, task]) => task.group === groupName);
        
        let updatedTasks = { ...prevTasks };
        
        // 기본 그룹으로 이동
        if (tasksInGroup.length > 0) {
          tasksInGroup.forEach(([taskId, task]) => {
            updatedTasks[taskId] = { ...task, group: '기본 그룹' };
          });
        }
        
        // 로컬 스토리지에 저장
        localStorage.setItem('tasks', JSON.stringify(updatedTasks));
        
        return updatedTasks;
      });
      
      // availableGroups에서 삭제
      setAvailableGroups(prevGroups => {
        const newGroups = prevGroups.filter(group => group !== groupName);
        
        // 로컬 스토리지에 저장
        localStorage.setItem('availableGroups', JSON.stringify(newGroups));
        
        return newGroups;
      });
      
      // 서버 API 호출 (아직 구현되지 않음)
      try {
        // 추후 API가 구현되면 해제
        /*
        await fetch(apiUrl('/api/groups/' + encodeURIComponent(groupName)), {
          method: 'DELETE'
        });
        */
      } catch (apiError) {
        console.warn('API 서버에 연결할 수 없습니다. 로컬에만 저장합니다.', apiError);
      }
      
      return { success: true, message: `'${groupName}' 그룹이 삭제되었습니다.` };
    } catch (error) {
      console.error('Error deleting group:', error);
      // 에러가 발생해도 UI에 에러를 표시하지 않고 작업 계속 진행
      setAvailableGroups(prevGroups => {
        const newGroups = prevGroups.filter(group => group !== groupName);
        
        // 로컬 스토리지에 저장
        localStorage.setItem('availableGroups', JSON.stringify(newGroups));
        
        return newGroups;
      });
      
      return { success: false, message: `오류가 발생했지만 '${groupName}' 그룹이 삭제되었습니다.` };
    }
  }, []);
