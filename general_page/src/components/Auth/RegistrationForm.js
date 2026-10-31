import React, { useState } from "react";
import InputMask from 'react-input-mask'
import { connect } from 'react-redux'
import fetch from '../functions/fetchWithTimeOut'
import {setLoading, setSignUpStage, setUser} from "../../actions";
import AlertText from "../Alert/AlertText";
import { csrf_token } from '../vars'

function RegistrationForm({setLoading, setUser, setSignUpStage}) {
    const [state, setState] = useState({
        stage: 'base_info',
        username: '',
        email: '',
        password: '',
        password2: '',
        surname: '',
        name: '',
        patronymic: '',
        birthdate: '',
        gender: '',
        phone: '',
        alert: {not_empty: false}
    })

    const usernameChange = (e) => setState((prev) => ({...prev, username: e.target.value})),
        emailChange = (e) => setState((prev) => ({...prev, email: e.target.value})),
        passwordChange = (e) => setState((prev) => ({...prev, password: e.target.value})),
        password2Change = (e) => setState((prev) => ({...prev, password2: e.target.value})),
        surnameChange = (e) => setState((prev) => ({...prev, surname: e.target.value})),
        nameChange = (e) => setState((prev) => ({...prev, name: e.target.value})),
        patronymicChange = (e) => setState((prev) => ({...prev, patronymic: e.target.value})),
        birthdateChange = (e) => setState((prev) => ({...prev, birthdate: e.target.value})),
        genderChange = (e) => setState((prev) => ({...prev, gender: e.target.value}))

    const handleSubmit = () => {
        setLoading(true)

        fetch('register123/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrf_token
            },
            body: 'user=' + encodeURIComponent(JSON.stringify(state))
        })
            .then(response => response.json())
            .then(response => {
                if (!response.error) {
                    setSignUpStage('confirm')
                    setUser({...response.user, password: state.password})
                } else {
                    setState((prev) => ({...prev, alert: {
                        not_empty: true,
                        type: 'alert-danger',
                        message: response.description
                    }}))

                    setTimeout(() => setState((prev) => ({
                        ...prev,
                        alert: {not_empty: false}
                    })), 2000)
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
            <h1 className="my-0">Registration</h1>
                {state.alert.not_empty && <AlertText message={state.alert.message} className={`alert ${state.alert.type} mt-1 mb-2`} />}
                <div className="mt-3" >
                    <div className="input-group">
                        <label htmlFor="username">Username</label>
                        <input type="text" id="username" onChange={usernameChange} />
                    </div>
                    <div className="input-group">
                        <label htmlFor="email">Email</label>
                        <input type="text" id="email" placeholder="email@example.com" onChange={emailChange} />
                    </div>
                    <div className="input-group">
                        <label htmlFor="password">Password</label>
                        <InputMask type="password" id="password" onChange={passwordChange} />
                    </div>
                    <div className="input-group">
                        <label htmlFor="password2">Repeat password</label>
                        <InputMask type="password" id="password2" onChange={password2Change} />
                    </div>
                    {state.stage === 'additional_info' &&
                        <React.Fragment>
                            <div className="input-group">
                                <label htmlFor="surname">surname}</label>
                                <input type="text" id="surname" value={state.surname} onChange={e => surnameChange(e)} />
                            </div>
                            <div className="input-group">
                                <label htmlFor="name">name</label>
                                <input type="text" id="name" value={state.name} onChange={e => nameChange(e)} />
                            </div>
                            <div className="input-group">
                                <label htmlFor="patronymic">patronymic</label>
                                <input type="text" id="patronymic" value={state.patronymic} onChange={e => patronymicChange(e)} />
                            </div>
                            <div className="input-group">
                                <label htmlFor="birthdate">birthdate</label>
                                <InputMask type="text" id="birthdate" mask="99.99.9999" onChange={birthdateChange} alwaysShowMask />
                            </div>
                            <div className="input-group">
                                <label htmlFor="gender">Gender</label>
                                <CustomSelect
                                    name='gender'
                                    onChange={selected => genderChange(selected)}
                                    id='gender'
                                    placeholder='Select...'
                                    options={['male', 'female']}
                                    classNamePrefix='custom-select'
                                />
                            </div>
                        </React.Fragment>
                    }
                    <button type="submit" className="btn btn-max btn-primary" onClick={(e) => handleSubmit()} >Submit</button>
                </div>
            </div>
        </React.Fragment>
    )
}

const mapStateToProps = store => {
    return {
        //
    }
}

const mapDispatchToProps = dispatch => {
    return {
        setLoading: loading => dispatch(setLoading(loading)),
        setUser: user => dispatch(setUser(user)),
        setSignUpStage: signup_stage => dispatch(setSignUpStage(signup_stage))
    }
}

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(RegistrationForm)
