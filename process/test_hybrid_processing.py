import asyncio
import time
import httpx
from models.processing_model import ProcessingRequest, MaterialRequest


async def test_hybrid_processing():
    """Test the hybrid processing approach with multiple materials"""
    # Create a processing request with multiple materials
    materials = [
        MaterialRequest(
            material_id="material_1",
            content="This is the first material content for processing.",
            content_type="text",
        ),
        MaterialRequest(
            material_id="material_2",
            content="This is the second material content for processing.",
            content_type="text",
        ),
        MaterialRequest(
            material_id="material_3",
            content="This is the third material content for processing.",
            content_type="text",
        ),
    ]

    request = ProcessingRequest(job_id="test_job_123", materials=materials)

    # Convert to dict for JSON serialization
    request_data = request.model_dump()

    # Call the processing service
    async with httpx.AsyncClient() as client:
        try:
            # Send processing request
            response = await client.post(
                "http://localhost:8001/api/v1/processing/", json=request_data
            )

            if response.status_code == 200:
                result = response.json()
                print("Processing result:")
                print(result)

                # Extract task IDs for status checking
                task_ids = []
                for material_result in result.get("results", []):
                    # In a real implementation, we would get task IDs from the response
                    # For this test, we'll simulate task IDs
                    task_ids.append(f"task_{material_result['material_id']}")

                # Test task status querying
                print("\nTesting task status queries:")
                for task_id in task_ids:
                    status_response = await client.get(
                        f"http://localhost:8001/api/v1/processing/task/{task_id}"
                    )
                    if status_response.status_code == 200:
                        status_result = status_response.json()
                        print(f"Task {task_id} status: {status_result}")
                    else:
                        print(f"Failed to get status for task {task_id}")

            else:
                print(
                    f"Processing request failed with status code: {response.status_code}"
                )
                print(response.text)

        except Exception as e:
            print(f"Error during testing: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_hybrid_processing())
