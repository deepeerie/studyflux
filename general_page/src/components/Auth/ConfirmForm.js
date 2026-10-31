import {setAuth, setLoading, setSignUpStage, setUser} from "../../actions";
import {connect} from "react-redux";
import AlertText from "../Alert/AlertText";
import React, {useState} from "react";
import fetch from "../functions/fetchWithTimeOut";
import { csrf_token } from '../vars'

function ConfirmForm({user, setSignUpStage, setLoading, setUser, setAuth}) {
    const [state, setState] = useState({
        confirm_code: '',
        alert: {not_empty: false}
    })

    const confirmCodeChange = (e) => setState((prev) => ({...prev, confirm_code: e.target.value}))

    const handleSubmit = () => {
        setLoading(true)

        fetch('register123/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrf_token
            },
            body: 'user=' + encodeURIComponent(JSON.stringify(user)) + '&confirm_code=' + state.confirm_code
        })
            .then(response => response.json())
            .then(response => {
                if (!response.error) {
                    setSignUpStage('signup_done')
                    setUser(response.user)
                    setAuth(true)
                } else {
                    setState((prev) => ({...prev, alert: {
                        not_empty: true,
                        type: 'alert-danger',
                        message: response.description
                    }}))

                    setTimeout(() => setState((prev) => ({
                        ...prev,
                        alert: {not_empty: false}
                    })), 5000)
                }

                setLoading(false)
            })
            .catch(err => {
                setLoading(false)
                setState((prev) => ({...prev, alert: {
                    not_empty: true,
                    type: 'alert-danger',
                    message: 'An error occured, please try later'
                }}))
            })
    }

    return (
        <React.Fragment>
            <div className="login-block wrapper fade_in_down">
            <h1 className="my-0">Confirm</h1>
                {state.alert.not_empty && <AlertText message={state.alert.message} className={`alert ${state.alert.type} mt-1 mb-2`} />}
                <div className="mt-3" >
                    <div className="input-group">
                        <label htmlFor="confirm_code">Confirm code</label>
                        <input type="text" id="confirm_code" onChange={confirmCodeChange} />
                    </div>
                    <button type="submit" className="btn btn-max btn-primary" onClick={(e) => handleSubmit()} >Submit</button>
                </div>
            </div>
        </React.Fragment>
    )
}

const mapStateToProps = store => {
    return {
        auth: store.auth,
        user: store.user,
    }
}

const mapDispatchToProps = dispatch => {
    return {
        setLoading: loading => dispatch(setLoading(loading)),
        setUser: user => dispatch(setUser(user)),
        setAuth: auth => dispatch(setAuth(auth)),
        setSignUpStage: signup_stage => dispatch(setSignUpStage(signup_stage))
    }
}

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(ConfirmForm)
