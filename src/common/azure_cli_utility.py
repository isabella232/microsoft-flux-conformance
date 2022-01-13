import subprocess

def create_flux_configuration(subscription_id, resource_group_name, cluster_type, cluster_name,
                                    configuration_name, repository_url, paths, namespace='default', branch='main',
                                    scope='cluster'):

    create_params = [
        'az',
        'k8s-configuration',
        'flux',
        'create',
        '--subscription',
        subscription_id,
        '-g',
        resource_group_name,
        '-c',
        cluster_name,
        '-n',
        configuration_name,
        '-t',
        cluster_type,
        '-u',
        repository_url,
        '--ns',
        namespace,
        '--branch',
        branch,
        '--scope',
        scope,
        '--no-wait'
    ]

    for i, path in enumerate(paths):
        create_params.append('--kustomization')
        create_params.append(f"name=kustomization{i}")
        create_params.append(f"path={path}")

    try:
        return subprocess.Popen(create_params, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    except Exception as e:
        pytest.fail("Error occurred while calling the creation of the flux configuration resource: " + str(e))