# vim: filetype=ruby

Vagrant.configure(2) do |config|
  config.vm.box = "ubuntu/trusty64"

  config.vm.network "private_network", type: "dhcp"
  # django server
  config.vm.network "forwarded_port", guest: 8080, host: 7080
  # celery flower dashboard
  config.vm.network "forwarded_port", guest: 5555, host: 8055


  config.vm.provision "shell", path: "provision-root.sh"
  config.vm.provision "shell", path: "provision-user.sh", privileged: false

  # setup and run celery upstart service
  config.vm.provision "shell", inline: "cp /vagrant/install/upstart-services/* /etc/init/"
  config.vm.provision "shell", inline: "service celery-service start"

  config.vm.synced_folder "dice_deploy_django", "/home/vagrant/dice_deploy_django"

  config.vm.provider "virtualbox" do |v|
    v.memory = 4096
    v.cpus = 1
  end
end
