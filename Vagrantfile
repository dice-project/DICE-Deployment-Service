# vim: filetype=ruby

Vagrant.configure(2) do |config|
  config.vm.box = "ubuntu/trusty64"

  config.vm.network "private_network", type: "dhcp"

  config.vm.network "forwarded_port", guest: 8080, host: 7080
  config.vm.network "forwarded_port", guest: 5555, host: 8055
  config.vm.network "forwarded_port", guest: 15672, host: 15672

  config.vm.provision "shell", path: "provision-root.sh"
  config.vm.provision "shell", path: "provision-user.sh", privileged: false

  config.vm.synced_folder "dice_deploy_django", "/home/vagrant/dice_deploy_django"
  config.vm.synced_folder "tests", "/home/vagrant/integration_tests"

  config.vm.provider "virtualbox" do |v|
    v.memory = 4096
    v.cpus = 1
  end
end
