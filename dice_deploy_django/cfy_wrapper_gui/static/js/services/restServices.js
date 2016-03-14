app.factory('RestServices', function ($resource) {
    return {
        containers: $resource(BASE_URL + '/containers', {}, {}),
        container: $resource(BASE_URL + '/containers/:id', {'id': '@id'}, {}),
        containerBlueprint: $resource(BASE_URL + '/containers/:id/blueprint', {'id': '@id'}, {
            put: {method: 'PUT'}
        }),
        blueprints: $resource(BASE_URL + '/blueprints', {}, {}),
        blueprint: $resource(BASE_URL + '/blueprints/:cfy_id', {'id': '@cfy_id'}, {}),
        output: $resource(BASE_URL + '/blueprints/:cfy_id/outputs', {'id': '@cfy_id'}, {})
    };
});

