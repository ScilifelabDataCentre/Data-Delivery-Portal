const vAccountHomeApp = {
    /* Main Account Home App */
    delimiters: ["[[", "]]"],
    data() {
        return {
            error_messages: [],
            account_info: null,
            account_data_loading: true
        }
    },
    methods: {
        fetchAccount() {
            axios
                .get('/user/account_methods')
                .then(response => {
                    console.log(response)
                    this.account_info = response.data
                    this.account_data_loading = false
                })
                .catch(error => {
                    this.error_messages.push('Unable to fetch account information')
                    this.account_data_loading = false
                })
        }
    }
}

const app = Vue.createApp(vAccountHomeApp)

app.component('v-account-home', {
    data() {
        return {
            new_name: {
                first: "",
                last: ""
            },
            hover: false
        }
    },
    computed: {
        account_info() { return this.$root.account_info }
    },
    created: function() {
        this.$root.fetchAccount();
    },
    methods: {
        submitNewName() {
            axios
                .put('/user/account_methods', {new_name: this.new_name})
                .then(response => {
                    console.log(response)
                })
                .catch(error => {
                    console.log(error)
                })
        }
    },
    template:
        /*html*/`
        <template v-if="this.$root.account_data_loading">
            <div class="spinner-grow" role="status"></div><span class="ml-3">Loading data...</span>
        </template>
        <template v-else>
            <template v-if="this.$root.any_errors">
                <template v-for="msg in this.$root.error_messages">
                    <div class="alert alert-danger" role="alert">
                    <h5 class="mt-2"><i class="far fa-exclamation-triangle mr-3"></i>{{msg}}</h5>
                    </div>
                </template>
            </template>
            <div class="container w-75 mx-auto bg-light mb-4 px-3 py-1">
                <div class="row my-3">
                    <div class="col-sm">
                        <b>Username</b>
                    </div>
                    <div class="col-sm">
                        {{ account_info.username }}
                    </div>
                    <div class="col-sm"></div>
                </div>
                <div class="row my-3">
                    <div class="col-sm">
                        <b>Name</b>
                    </div>
                    <div class="col-sm">
                        {{ account_info.first_name }} {{ account_info.last_name }}
                    </div>
                    <div class="col-sm" @mouseover="hover = true" @mouseleave="hover = false">
                            <button class="btn btn-sm btn-outline-info float-end px-1 mx-1 py-0">
                                <i class="far fa-user-edit"></i>
                            </button>
                            <small v-if="hover" class="card float-end py-0 px-1" display="inline-block" style="position: absolute;">
                                Edit
                            </small>
                    </div>
                </div>
                <template v-for="(email, i) in account_info.emails" :key="email">
                    <div class="row my-2">
                        <div class="col-sm">
                            <b v-if="i==0">Email</b>
                        </div>
                        <div class="col-sm">
                            {{ email.address }}
                            <template v-if="email.primary==true && account_info.emails.length>1">
                                <span class="badge bg-info mx-2 px-1 me-2 ">Primary</span>
                            </template>
                        </div>
                        <div class="col-sm">
                            <template v-if="account_info.emails.length>1">
                                <button class="btn btn-sm btn-outline-danger float-end px-1 mx-1 py-0" :disabled="email.primary==true">
                                    <i class="far fa-trash-can px-1"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-info float-end px-1 mx-1 py-0" :disabled="email.primary==true">
                                    <i class="far fa-thumb-tack px-1"></i>
                                </button>
                            </template>
                        </div>
                    </div>
                </template>
                <form method="PUT" action="" class="needs-validation" novalidate>
                    <div class="row my-2">
                        <div class="col-sm"></div>
                        <div class="col-sm">
                            <input type="email" class="form-control form-control-sm" placeholder="Add New Email" required>
                        </div>
                        <div class="col-sm">
                                <button type="submit" class="btn btn-sm btn-outline-info float-end px-1 mx-1 py-0">
                                    <i class="far fa-plus mx-1"></i>
                                </button>
                        </div>
                    </div>
                </form>
                <div class="row my-2">
                    <div class="col-sm">
                        <b>Password</b>
                    </div>
                    <div class="col-sm">
                        ************
                    </div>
                    <div class="col-sm">
                        <button class="btn btn-sm btn-outline-info float-end px-1 mx-1 py-0">
                        <i class="far fa-lock px-1"></i>
                        </button>
                    </div>
                </div>
            </div>
        </template>
        `
    }
)

// app.component('v-account-response', {
//     template:
//         /*html*/`
//         <!-- Response messages -->
//         <div id="response-container" class="alert alert-dismissible fade show my-4 d-none">
//             <span></span>
//             <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
//         </div>
//         `
// } )

app.mount('#account-vue-start-point')
