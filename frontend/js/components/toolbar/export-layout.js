Vue.component("export-layout", {
    props: ["gephi_json"],
    data: function() {
        return  {
            message: "",
            terms: []
        }
    },
    methods: {
        export_graph: function() {
            var com = this;

            let dataStr = JSON.stringify(com.gephi_json);
            let dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
        
            let exportFileDefaultName = 'data.json';
        
            let linkElement = document.createElement('a');
            linkElement.setAttribute('href', dataUri);
            linkElement.setAttribute('download', exportFileDefaultName);
            linkElement.click();
        },
    },
    mounted: function() {
        var com = this;

    },
    template: `
        <div v-show="gephi_json != null" class="toolbar-button">
            <div class="toolbar-theme">
                <button v-on:click="export_graph()" id="export_json">Export Data</button>
                <span class="toolbar-icon">&#8681;</span>
            </div>
        </div>
    `
});