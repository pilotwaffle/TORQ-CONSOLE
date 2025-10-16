    async def _execute_n8n_workflow(
        self,
        action: str,
        workflow_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute n8n workflow automation operations.

        Args:
            action: Operation to perform (list_workflows, trigger_workflow,
                    get_workflow_status, get_workflow_result)
            workflow_id: Workflow ID (required for trigger_workflow)
            execution_id: Execution ID (required for status/result queries)
            data: Data payload for workflow trigger
            **kwargs: Additional parameters

        Returns:
            Dict with success status and operation results
        """
        import time
        start_time = time.time()

        # Update tool performance
        self.tool_performance['n8n_workflow']['usage_count'] += 1

        if not N8N_WORKFLOW_AVAILABLE:
            error_msg = "N8N Workflow Tool not available. Install httpx: pip install httpx"
            self.logger.error(f"[N8N] {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'action': action,
                'execution_time': time.time() - start_time
            }

        try:
            self.logger.info(f"[N8N] Executing action: {action}")

            # Create N8N workflow tool
            n8n_tool = create_n8n_workflow_tool()

            # Check availability
            if not n8n_tool.is_available():
                error_msg = ("N8N Workflow Tool not configured. Set N8N_API_URL and N8N_API_KEY "
                            "environment variables, or connect MCP n8n server.")
                self.logger.warning(f"[N8N] {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'action': action,
                    'execution_time': time.time() - start_time
                }

            # Execute workflow operation
            result = await n8n_tool.execute(
                action=action,
                workflow_id=workflow_id,
                execution_id=execution_id,
                data=data,
                **kwargs
            )

            execution_time = time.time() - start_time
            result['execution_time'] = execution_time

            # Update success stats
            if result.get('success'):
                self.tool_performance['n8n_workflow']['success_count'] += 1
                self.tool_performance['n8n_workflow']['total_time'] += execution_time

                # Log success based on action type
                if action == 'list_workflows':
                    count = result.get('result', {}).get('count', 0)
                    self.logger.info(f"[N8N] ✓ SUCCESS - Listed {count} workflows")
                elif action == 'trigger_workflow':
                    exec_id = result.get('result', {}).get('execution_id', 'N/A')
                    self.logger.info(f"[N8N] ✓ SUCCESS - Triggered workflow {workflow_id}, execution: {exec_id}")
                elif action == 'get_workflow_status':
                    status = result.get('result', {}).get('status', 'unknown')
                    self.logger.info(f"[N8N] ✓ SUCCESS - Execution {execution_id} status: {status}")
                elif action == 'get_workflow_result':
                    status = result.get('result', {}).get('status', 'unknown')
                    finished = result.get('result', {}).get('finished', False)
                    self.logger.info(f"[N8N] ✓ SUCCESS - Execution {execution_id} finished: {finished}, status: {status}")
            else:
                self.logger.error(f"[N8N] ✗ FAILED: {result.get('error')}")

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"N8N workflow operation error: {str(e)}"
            self.logger.error(f"[N8N] ✗ ERROR: {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'action': action,
                'execution_time': execution_time
            }
