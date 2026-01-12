import argparse
import dotenv
import os
import sys
from   azure.identity        import DefaultAzureCredential
from   azure.mgmt.compute    import ComputeManagementClient
from   azure.core.exceptions import AzureError
from   azure.mgmt.resource   import ResourceManagementClient

# Load environment variables
dotenv.load_dotenv()

SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")
RESOURCE_GROUP  = os.getenv("AZURE_RESOURCE_GROUP")
VIRTUAL_MACHINE = os.getenv("AZURE_VIRTUAL_MACHINE")

def get_compute_client():
     return ComputeManagementClient(DefaultAzureCredential(), SUBSCRIPTION_ID)

def get_vm_status(client):
     try:
          vm = client.virtual_machines.instance_view(RESOURCE_GROUP, VIRTUAL_MACHINE)
          for status in vm.statuses:
               if "PowerState" in status.code:
                    return status.display_status
          return "unknown"
     except AzureError as e:
          print(f"[error]: {e.message.lower()}")
          sys.exit(1)

def start_vm():
     client = get_compute_client()
     status = get_vm_status(client)
     if status == "VM running":
          print(f"[warn] vm='{VIRTUAL_MACHINE} is already running.")
          return

     async_poller = client.virtual_machines.begin_start(RESOURCE_GROUP, VIRTUAL_MACHINE)
     async_poller.result()
     print(f"[info] vm {VIRTUAL_MACHINE} started successfully.")

def stop_vm():
     client = get_compute_client()
     status = get_vm_status(client)
     if "deallocated" in status.lower():
          print(f"[warn] vm {VIRTUAL_MACHINE} is already deallocated.")
          return

     async_poller = client.virtual_machines.begin_deallocate(RESOURCE_GROUP, VIRTUAL_MACHINE)
     async_poller.result() 
     print(f"[info] vm {VIRTUAL_MACHINE} deallocated successfully.")

def debug_vm():
     client = get_compute_client()
     try:
          vm           = client.virtual_machines.get(RESOURCE_GROUP, VIRTUAL_MACHINE)
          vm_size_name = vm.hardware_profile.vm_size
          skus         = client.resource_skus.list(filter=f"location eq '{vm.location}'")
          cpu          = "n/a"
          ram          = "n/a"
          
          for sku in skus:
               if sku.name == vm_size_name:
                    for capability in sku.capabilities:
                         if capability.name == "vCPUs":
                              cpu = capability.value
                         if capability.name == "MemoryGB":
                              ram = capability.value

          print(f"[info] specs {VIRTUAL_MACHINE}:")
          print(f"  > location:        {vm.location.lower()}")
          print(f"  > size:            {vm_size_name.lower()}")
          print(f"  > cpu (vcpus):     {cpu}")
          print(f"  > ram (gb):        {ram}")
          print(f"  > disk size (gb):  {vm.storage_profile.os_disk.disk_size_gb}")
          print(f"  > os type:         {vm.storage_profile.os_disk.os_type.lower()}")
          print(f"  > provision state: {vm.provisioning_state.lower()}")
          print(f"  > vm id:           {vm.vm_id}")
          
     except AzureError as e:
          print(f"[error] {e.message.lower()}")

def main():
     parser = argparse.ArgumentParser()
     parser.add_argument("--action", choices=["start", "stop", "debug"], required=True)

     args = parser.parse_args()

     try:
          if args.action == "start":
               start_vm()
          elif args.action == "stop":
               stop_vm()
          elif args.action == "debug":
               debug_vm()
     except AzureError as e:
          print(f"[error]: {e.message.lower()}")
     except Exception as e:
          print(f"[error]: {e.message.lower()}")

if __name__ == "__main__":
    main()